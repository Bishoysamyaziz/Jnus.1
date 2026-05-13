"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const C = {
  ink:     '#09090F',
  ink2:    '#0D0D16',
  paper:   '#F5F3EF',
  gold:    '#C9A84C',
  gold2:   '#E8CC80',
  golddim: '#C9A84C18',
  stone:   '#6B6860',
  stone2:  '#9C9888',
  line:    '#E2DDD6',
  line2:   '#2A2820',
  txt:     '#1A1814',
  muted:   '#6B6860',
  dim:     '#C8C4BC',
  green:   '#3D9970',
  red:     '#C0392B',
};

const MODES = [
  { id: "build",   name: "Build",   icon: "🚀", desc: "Generate new project" },
  { id: "fix",     name: "Fix",     icon: "🔧", desc: "Fix/refactor code" },
  { id: "explain", name: "Explain", icon: "💡", desc: "Explain code" },
];

// ── SSE STREAMING ───────────────────────────────────────────
async function* streamChat(message: string, mode: string) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6).trim();
        if (data === "[DONE]") return;

        try {
          const parsed = JSON.parse(data);
          if (parsed.type && parsed.content) {
            yield parsed;
          }
        } catch {
          // Skip malformed
        }
      }
    }
  }
}

// ── RUN TASK ───────────────────────────────────────────
async function runTask(message: string, mode: string, token?: string) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_URL}/run`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message, mode }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ── AUTH ───────────────────────────────────────────
function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("oneagent_token");
  }
  return null;
}

function setToken(token: string) {
  localStorage.setItem("oneagent_token", token);
}

// ── COMPONENTS ──────────────────────────────────────

function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: 5, alignItems: "center", padding: "4px 0" }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 6, height: 6, borderRadius: "50%", background: C.gold,
          opacity: 0.7, animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

function Message({ msg }: { msg: any }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex", gap: 12, marginBottom: 20,
      flexDirection: isUser ? "row-reverse" : "row",
      animation: "fadeUp 0.3s ease",
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 11,
        background: isUser ? C.gold : C.ink,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 13, color: isUser ? C.ink : C.gold,
        fontFamily: "'Playfair Display', serif", fontWeight: 700,
        flexShrink: 0,
      }}>
        {isUser ? "U" : "J"}
      </div>
      <div style={{
        padding: "12px 16px",
        borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
        background: isUser ? C.ink : "#fff",
        border: `1px solid ${isUser ? C.line2 : C.line}`,
        color: isUser ? C.paper : C.txt,
        fontSize: 13, lineHeight: 1.8,
        maxWidth: "80%",
        whiteSpace: "pre-wrap",
        fontFamily: "'Noto Kufi Arabic', sans-serif",
      }}>
        {msg.content}
        {msg.streaming && <TypingIndicator />}
      </div>
    </div>
  );
}

// ── MAIN COMPONENT ──────────────────────────────────

export default function OneAgentOS() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<any[]>([
    { id: 1, role: "assistant", content: "Welcome to OneAgent OS! Type a prompt to build, fix, or explain code.", streaming: false },
  ]);
  const [thinking, setThinking] = useState(false);
  const [mode, setMode] = useState("build");
  const [token, setTokenState] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showAuth, setShowAuth] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const t = getToken();
    if (t) setTokenState(t);
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || thinking) return;

    const userMsg = { id: Date.now(), role: "user", content: input, streaming: false };
    const assistantId = Date.now() + 1;
    const assistantMsg = { id: assistantId, role: "assistant", content: "", streaming: true };

    setMessages((prev: any[]) => [...prev, userMsg, assistantMsg]);
    setThinking(true);
    setLogs([]);
    setResult(null);

    const prompt = input;
    setInput("");

    try {
      let fullContent = "";
      for await (const chunk of streamChat(prompt, mode)) {
        if (chunk.type === "token") {
          fullContent += chunk.content;
          setMessages((prev: any[]) => prev.map((m: any) =>
            m.id === assistantId ? { ...m, content: fullContent, streaming: true } : m
          ));
        } else if (chunk.type === "status") {
          setMessages((prev: any[]) => prev.map((m: any) =>
            m.id === assistantId ? { ...m, content: fullContent + "\n⏳ " + chunk.content, streaming: true } : m
          ));
        } else if (chunk.type === "error") {
          setMessages((prev: any[]) => prev.map((m: any) =>
            m.id === assistantId ? { ...m, content: fullContent + "\n❌ " + chunk.content, streaming: false } : m
          ));
        } else if (chunk.type === "done") {
          setMessages((prev: any[]) => prev.map((m: any) =>
            m.id === assistantId ? { ...m, content: fullContent + "\n\n✅ " + chunk.content, streaming: false } : m
          ));
        } else if (chunk.type === "files") {
          const files = Array.isArray(chunk.content) ? chunk.content : [];
          if (files.length > 0) {
            setMessages((prev: any[]) => prev.map((m: any) =>
              m.id === assistantId ? { ...m, content: fullContent + "\n\n📁 Files: " + files.join(", "), streaming: false } : m
            ));
          }
        }
      }
    } catch (err: any) {
      setMessages((prev: any[]) => prev.map((m: any) =>
        m.id === assistantId ? { ...m, content: "⚠️ Error: " + (err.message || "Connection failed"), streaming: false } : m
      ));
    }

    setThinking(false);
  };

  const handleRun = async () => {
    if (!input.trim() || thinking) return;

    setLogs(["🚀 Starting task..."]);
    setResult(null);

    try {
      const res = await runTask(input, mode, token || undefined);
      setLogs(res.logs || []);
      setResult(res);
      setMessages((prev: any[]) => [...prev, {
        id: Date.now(),
        role: "assistant",
        content: `✅ Task completed!\n\n📁 Files: ${(res.files || []).join(", ") || "None"}\n⏱️ Duration: ${res.duration}s\n📋 Task ID: ${res.task_id}`,
        streaming: false,
      }]);
    } catch (err: any) {
      setLogs([`❌ Error: ${err.message}`]);
      setMessages((prev: any[]) => [...prev, {
        id: Date.now(),
        role: "assistant",
        content: "❌ Error: " + err.message + "\n\n💡 Tip: You need to login first. Click 'Login' button.",
        streaming: false,
      }]);
    }
  };

  const handleLogin = async () => {
    try {
      const res = await fetch(`${API_URL}/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
        method: "POST",
      });
      const data = await res.json();
      setToken(data.access_token);
      setTokenState(data.access_token);
      setShowAuth(false);
      setMessages((prev: any[]) => [...prev, {
        id: Date.now(), role: "assistant",
        content: "✅ Logged in successfully! You can now run tasks.",
        streaming: false,
      }]);
    } catch (err: any) {
      alert("Login failed: " + err.message);
    }
  };

  const handleRegister = async () => {
    try {
      const res = await fetch(`${API_URL}/auth/register?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
        method: "POST",
      });
      const data = await res.json();
      setToken(data.access_token);
      setTokenState(data.access_token);
      setShowAuth(false);
      setMessages((prev: any[]) => [...prev, {
        id: Date.now(), role: "assistant",
        content: "✅ Registered and logged in! You can now run tasks.",
        streaming: false,
      }]);
    } catch (err: any) {
      alert("Registration failed: " + err.message);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Noto+Kufi+Arabic:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.paper}; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${C.line}; border-radius: 2px; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-5px); } }
        textarea { outline: none; resize: none; }
      `}</style>

      <div style={{
        display: "flex", height: "100vh",
        fontFamily: "'Noto Kufi Arabic', sans-serif",
        background: C.paper, color: C.txt,
        direction: "rtl", overflow: "hidden",
      }}>
        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {/* Header */}
          <div style={{
            padding: "12px 20px", borderBottom: `1px solid ${C.line}`,
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(245,243,239,.95)", backdropFilter: "blur(10px)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                width: 7, height: 7, borderRadius: "50%", background: C.green,
                boxShadow: `0 0 8px ${C.green}`, display: "inline-block",
              }} />
              <span style={{ fontSize: 11, color: C.muted, fontFamily: "'DM Mono', monospace" }}>
                OneAgent OS
              </span>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {!token ? (
                <button onClick={() => setShowAuth(!showAuth)} style={{
                  padding: "5px 12px", background: C.ink, color: C.paper,
                  border: "none", borderRadius: 6, fontSize: 10, cursor: "pointer",
                  fontFamily: "'DM Mono', monospace",
                }}>Login</button>
              ) : (
                <span style={{ fontSize: 9, color: C.green, fontFamily: "'DM Mono', monospace" }}>
                  ✓ Authenticated
                </span>
              )}
              <a href="/" style={{
                padding: "5px 12px", border: `1px solid ${C.line}`, borderRadius: 6,
                fontSize: 10, color: C.muted, cursor: "pointer", textDecoration: "none",
                fontFamily: "'DM Mono', monospace",
              }}>← Home</a>
            </div>
          </div>

          {/* Auth Modal */}
          {showAuth && (
            <div style={{
              position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
              display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
            }}>
              <div style={{
                background: C.paper, padding: 32, borderRadius: 16,
                border: `1px solid ${C.line}`, width: 360,
              }}>
                <h3 style={{ marginBottom: 20, fontFamily: "'Playfair Display', serif" }}>Login / Register</h3>
                <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email"
                  style={{ width: "100%", padding: 10, marginBottom: 10, borderRadius: 8, border: `1px solid ${C.line}`, fontSize: 13 }} />
                <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="Password"
                  style={{ width: "100%", padding: 10, marginBottom: 16, borderRadius: 8, border: `1px solid ${C.line}`, fontSize: 13 }} />
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={handleLogin} style={{
                    flex: 1, padding: 10, background: C.ink, color: C.paper,
                    border: "none", borderRadius: 8, cursor: "pointer", fontSize: 12,
                  }}>Login</button>
                  <button onClick={handleRegister} style={{
                    flex: 1, padding: 10, background: C.gold, color: C.ink,
                    border: "none", borderRadius: 8, cursor: "pointer", fontSize: 12,
                  }}>Register</button>
                </div>
                <button onClick={() => setShowAuth(false)} style={{
                  marginTop: 12, padding: "6px 16px", background: "transparent",
                  border: `1px solid ${C.line}`, borderRadius: 6, cursor: "pointer",
                  fontSize: 10, width: "100%",
                }}>Close</button>
              </div>
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "24px 32px" }}>
            {messages.map((msg: any) => <Message key={msg.id} msg={msg} />)}
            <div ref={messagesEndRef} />
          </div>

          {/* Logs Panel */}
          {logs.length > 0 && (
            <div style={{
              maxHeight: 150, overflowY: "auto", padding: "8px 20px",
              background: C.ink, color: C.green, fontFamily: "'DM Mono', monospace",
              fontSize: 10, lineHeight: 1.8, borderTop: `1px solid ${C.line2}`,
            }}>
              {logs.map((log, i) => <div key={i}>{log}</div>)}
            </div>
          )}

          {/* Result Card */}
          {result && (
            <div style={{
              padding: "12px 20px", background: C.golddim,
              borderTop: `1px solid ${C.gold}`, fontSize: 11, color: C.txt,
            }}>
              ✅ Task: {result.task_id} | Status: {result.status} | Duration: {result.duration}s
              {result.files?.length > 0 && <span> | Files: {result.files.length}</span>}
            </div>
          )}

          {/* Input */}
          <div style={{ padding: "14px 20px 18px", borderTop: `1px solid ${C.line}`, background: "rgba(245,243,239,.97)" }}>
            {/* Mode pills */}
            <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
              {MODES.map(m => (
                <button key={m.id} onClick={() => setMode(m.id)} style={{
                  padding: "5px 10px", borderRadius: 8,
                  border: `1px solid ${mode === m.id ? C.gold + "60" : C.line}`,
                  background: mode === m.id ? C.golddim : "transparent",
                  cursor: "pointer", fontSize: 11, color: mode === m.id ? C.gold : C.muted,
                  fontFamily: "'DM Mono', monospace",
                }}>
                  {m.icon} {m.name}
                </button>
              ))}
              <button onClick={handleRun} disabled={!input.trim() || thinking} style={{
                padding: "5px 14px", borderRadius: 8,
                background: input.trim() && !thinking ? C.green : C.line,
                border: "none", color: input.trim() && !thinking ? "#fff" : C.dim,
                cursor: input.trim() && !thinking ? "pointer" : "not-allowed",
                fontSize: 11, fontFamily: "'DM Mono', monospace", marginRight: "auto",
              }}>
                ▶ Run & Deploy
              </button>
            </div>

            {/* Input box */}
            <div style={{
              display: "flex", gap: 10, alignItems: "flex-end",
              padding: "10px 14px", borderRadius: 16,
              border: `1.5px solid ${input ? C.gold : C.line}`,
              background: "#fff", transition: "border-color 0.2s",
            }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your prompt here... (Enter to send)"
                rows={1}
                style={{
                  flex: 1, background: "transparent", border: "none",
                  color: C.txt, fontSize: 13, lineHeight: 1.6,
                  fontFamily: "'Noto Kufi Arabic', sans-serif",
                  maxHeight: 120, overflowY: "auto",
                }}
              />
              <button onClick={sendMessage} disabled={!input.trim() || thinking} style={{
                width: 36, height: 36, borderRadius: 10, border: "none",
                background: input.trim() && !thinking ? C.ink : C.line,
                color: input.trim() && !thinking ? C.gold : C.dim,
                cursor: input.trim() && !thinking ? "pointer" : "not-allowed",
                fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center",
              }}>↑</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
