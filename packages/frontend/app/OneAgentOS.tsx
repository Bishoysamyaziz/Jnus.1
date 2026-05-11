"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ||
                "http://localhost:8000";

// ── JNUS PALETTE ──────────────────────────────────────────────────
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

// ── AGENT FRAMEWORKS ─────────────────────────────────────────────
const AGENTS = [
  { id: "auto",        name: "Auto",        icon: "◈", color: C.gold,   desc: "اختيار تلقائي" },
  { id: "crewai",      name: "CrewAI",       icon: "⬡", color: "#3DD6C0", desc: "Multi-role" },
  { id: "autogen",     name: "AutoGen",      icon: "◉", color: C.gold,   desc: "Group chat" },
  { id: "metagpt",     name: "MetaGPT",      icon: "▣", color: "#F06292", desc: "Software Co." },
  { id: "langchain",   name: "LangChain",    icon: "⟁", color: "#7B6EF6", desc: "Chain of thought" },
  { id: "aider",       name: "Aider",        icon: "⌬", color: C.green,  desc: "Code editing" },
];

const INTENTS = [
  { type: "CODE",         label: "كود",       color: C.green,  icon: "⌨" },
  { type: "RESEARCH",     label: "بحث",       color: "#3DD6C0", icon: "◎" },
  { type: "CREATIVE",     label: "إبداعي",    color: "#F06292", icon: "✦" },
  { type: "DATA",         label: "بيانات",    color: C.gold,   icon: "▦" },
  { type: "PLANNING",     label: "تخطيط",     color: "#7B6EF6", icon: "◈" },
  { type: "AUTOMATION",   label: "أتمتة",     color: "#F5A623", icon: "⚡" },
];

const SAMPLE_CONVOS = [
  { id: 1, title: "بناء REST API للـ authentication", intent: "CODE",     time: "منذ ساعتين" },
  { id: 2, title: "تحليل بيانات المبيعات Q1",          intent: "DATA",     time: "أمس" },
  { id: 3, title: "خطة تسويق لمنتج SaaS",              intent: "PLANNING", time: "منذ يومين" },
];

// ── API CONFIGURATION ──────────────────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── SSE STREAMING CLIENT ───────────────────────────────────────────
async function* streamChat(message: string, sessionId: string) {
  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-s4",
      messages: [{ role: "user", content: message }],
      stream: true,
      session_id: sessionId,
      user_id: "anonymous",
    }),
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
          const content = parsed.choices?.[0]?.delta?.content || "";
          if (content) {
            yield { type: "token", content };
          }
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

// ── COMPONENTS ────────────────────────────────────────────────────

function Dot({ color, pulse }: { color: string; pulse?: boolean }) {
  return (
    <span style={{
      display: "inline-block",
      width: 7, height: 7,
      borderRadius: "50%",
      background: color,
      boxShadow: pulse ? `0 0 8px ${color}` : "none",
      animation: pulse ? "pulse 1.5s ease-in-out infinite" : "none",
      flexShrink: 0,
    }} />
  );
}

function AgentBadge({ agent, active, onClick }: { agent: typeof AGENTS[0]; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 6,
      padding: "5px 10px",
      borderRadius: 8,
      border: `1px solid ${active ? agent.color + "60" : C.line}`,
      background: active ? agent.color + "12" : "transparent",
      cursor: "pointer",
      transition: "all 0.15s ease",
    }}>
      <span style={{ fontSize: 13, color: agent.color }}>{agent.icon}</span>
      <span style={{ fontSize: 11, color: active ? agent.color : C.muted, fontFamily: "'DM Mono', monospace" }}>
        {agent.name}
      </span>
    </button>
  );
}

function IntentTag({ intent }: { intent: string }) {
  const info = INTENTS.find(i => i.type === intent);
  if (!info) return null;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px",
      borderRadius: 5,
      background: info.color + "15",
      border: `1px solid ${info.color}30`,
      fontSize: 10,
      color: info.color,
      fontFamily: "'DM Mono', monospace",
      letterSpacing: 0.5,
    }}>
      {info.icon} {info.label}
    </span>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: 5, alignItems: "center", padding: "4px 0" }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 6, height: 6,
          borderRadius: "50%",
          background: C.gold,
          opacity: 0.7,
          animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

function MessageContent({ content, streaming }: { content: string; streaming?: boolean }) {
  const lines = content.split("\n");
  const rendered: React.ReactNode[] = [];
  let inCode = false;
  let codeLines: string[] = [];
  let codeLang = "";

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("```")) {
      if (!inCode) {
        inCode = true;
        codeLang = line.slice(3);
        codeLines = [];
      } else {
        rendered.push(
          <div key={`code-${i}`} style={{
            margin: "10px 0",
            borderRadius: 10,
            overflow: "hidden",
            border: `1px solid ${C.line}`,
          }}>
            {codeLang && (
              <div style={{
                padding: "6px 14px",
                background: C.ink2,
                borderBottom: `1px solid ${C.line2}`,
                fontSize: 10,
                color: C.stone2,
                fontFamily: "'DM Mono', monospace",
                display: "flex", justifyContent: "space-between",
              }}>
                <span>{codeLang}</span>
                <span style={{ color: C.green, letterSpacing: 0.5 }}>● LIVE</span>
              </div>
            )}
            <pre style={{
              margin: 0, padding: "14px",
              background: C.ink2,
              fontSize: 12,
              lineHeight: 1.7,
              color: "#7DD3FC",
              fontFamily: "'DM Mono', monospace",
              overflowX: "auto",
            }}>{codeLines.join("\n")}</pre>
          </div>
        );
        inCode = false;
        codeLines = [];
        codeLang = "";
      }
    } else if (inCode) {
      codeLines.push(line);
    } else if (line.startsWith("**") && line.endsWith("**")) {
      rendered.push(
        <strong key={i} style={{ color: C.gold, display: "block", margin: "6px 0 2px" }}>
          {line.slice(2, -2)}
        </strong>
      );
    } else if (line.match(/^\d\./)) {
      rendered.push(
        <div key={i} style={{ display: "flex", gap: 8, margin: "3px 0", fontSize: 13, color: C.txt }}>
          <span style={{ color: C.gold, fontFamily: "'DM Mono', monospace", minWidth: 16 }}>
            {line[0]}
          </span>
          <span>{line.slice(2).replace(/\*\*(.*?)\*\*/g, "$1")}</span>
        </div>
      );
    } else if (line === "") {
      rendered.push(<div key={i} style={{ height: 6 }} />);
    } else {
      const parts = line.split(/\*\*(.*?)\*\*/g);
      rendered.push(
        <span key={i} style={{ fontSize: 13, lineHeight: 1.8, color: C.txt, display: "block" }}>
          {parts.map((p, j) => j % 2 === 0
            ? <span key={j}>{p}</span>
            : <strong key={j} style={{ color: C.gold }}>{p}</strong>
          )}
        </span>
      );
    }
  }

  return (
    <div>
      {rendered}
      {streaming && <TypingIndicator />}
    </div>
  );
}

function Message({ msg }: { msg: any }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      flexDirection: isUser ? "row-reverse" : "row",
      gap: 12,
      marginBottom: 24,
      animation: "fadeUp 0.3s ease",
    }}>
      {/* Avatar */}
      <div style={{
        width: 32, height: 32,
        borderRadius: isUser ? 10 : 11,
        background: isUser ? C.golddim : C.ink,
        border: `1px solid ${isUser ? C.gold : C.line2}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 13,
        flexShrink: 0,
        color: isUser ? C.gold : C.gold,
        fontFamily: isUser ? "'Noto Kufi Arabic', sans-serif" : "'Playfair Display', serif",
        fontWeight: 700,
      }}>
        {isUser ? "أ" : "J"}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: "78%", minWidth: 60 }}>
        {!isUser && msg.intent && (
          <div style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <IntentTag intent={msg.intent} />
            {msg.agent && (
              <span style={{
                fontSize: 10, color: C.muted,
                fontFamily: "'DM Mono', monospace",
              }}>via {msg.agent}</span>
            )}
            {msg.duration && (
              <span style={{ fontSize: 10, color: C.dim, fontFamily: "'DM Mono', monospace" }}>
                {msg.duration}
              </span>
            )}
          </div>
        )}
        <div style={{
          padding: isUser ? "10px 14px" : "12px 16px",
          borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
          background: isUser ? C.ink : "#fff",
          border: `1px solid ${isUser ? C.line2 : C.line}`,
          fontSize: 13,
          lineHeight: 1.7,
          color: isUser ? C.paper : C.txt,
        }}>
          {isUser
            ? <span>{msg.content}</span>
            : <MessageContent content={msg.content} streaming={msg.streaming} />
          }
        </div>
        {!isUser && msg.cost && (
          <div style={{ marginTop: 5, display: "flex", gap: 10 }}>
            <span style={{ fontSize: 10, color: C.dim, fontFamily: "'DM Mono', monospace" }}>
              ${msg.cost} · {msg.tokens} tokens
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function Sidebar({ conversations, activeId, onSelect, onNew }: {
  conversations: typeof SAMPLE_CONVOS;
  activeId: number;
  onSelect: (id: number) => void;
  onNew: () => void;
}) {
  return (
    <div style={{
      width: 240,
      background: C.ink2,
      borderLeft: `1px solid ${C.line2}`,
      display: "flex", flexDirection: "column",
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{
        padding: "18px 16px 14px",
        borderBottom: `1px solid ${C.line2}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            fontFamily: "'Playfair Display', serif", fontSize: 16, fontWeight: 900, color: C.paper,
          }}>
            J<em style={{ color: C.gold, fontStyle: 'normal' }}>nus</em>
          </div>
        </div>
      </div>

      {/* New Chat */}
      <div style={{ padding: "10px 10px 6px" }}>
        <button onClick={onNew} style={{
          width: "100%",
          padding: "8px 12px",
          borderRadius: 9,
          border: `1px dashed #2E2C22`,
          background: "transparent",
          color: C.stone2,
          fontSize: 12,
          cursor: "pointer",
          display: "flex", alignItems: "center", gap: 6,
          transition: "all 0.15s",
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.gold; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = "#2E2C22"; e.currentTarget.style.color = C.stone2; }}
        >
          <span style={{ fontSize: 16, lineHeight: 1 }}>+</span>
          محادثة جديدة
        </button>
      </div>

      {/* History */}
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 10px" }}>
        <div style={{ fontSize: 9, color: "#3A3828", letterSpacing: 1.5, padding: "8px 6px 4px", fontFamily: "'DM Mono', monospace" }}>
          RECENT
        </div>
        {conversations.map(c => (
          <button key={c.id} onClick={() => onSelect(c.id)} style={{
            width: "100%", textAlign: "right",
            padding: "8px 8px",
            borderRadius: 8,
            border: "1px solid transparent",
            background: activeId === c.id ? "#141410" : "transparent",
            cursor: "pointer",
            marginBottom: 2,
            transition: "all 0.12s",
          }}
            onMouseEnter={e => { if (activeId !== c.id) e.currentTarget.style.background = "#141410"; }}
            onMouseLeave={e => { if (activeId !== c.id) e.currentTarget.style.background = "transparent"; }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
              <IntentTag intent={c.intent} />
            </div>
            <div style={{ fontSize: 11, color: activeId === c.id ? C.stone2 : C.stone2, marginTop: 4, lineHeight: 1.4, textAlign: "right" }}>
              {c.title}
            </div>
            <div style={{ fontSize: 9, color: "#3A3828", marginTop: 3, fontFamily: "'DM Mono', monospace" }}>
              {c.time}
            </div>
          </button>
        ))}
      </div>

      {/* Footer stats */}
      <div style={{
        padding: "10px 14px",
        borderTop: `1px solid ${C.line2}`,
        display: "flex", flexDirection: "column", gap: 5,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 9, color: "#3A3828", fontFamily: "'DM Mono', monospace" }}>تكلفة اليوم</span>
          <span style={{ fontSize: 9, color: C.green, fontFamily: "'DM Mono', monospace" }}>$0.003</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 9, color: "#3A3828", fontFamily: "'DM Mono', monospace" }}>النموذج</span>
          <span style={{ fontSize: 9, color: C.gold, fontFamily: "'DM Mono', monospace" }}>تلقائي</span>
        </div>
      </div>
    </div>
  );
}

function AgentPanel({ activeAgent, onSelect, thinking, currentAgent }: {
  activeAgent: string;
  onSelect: (id: string) => void;
  thinking: boolean;
  currentAgent: string;
}) {
  return (
    <div style={{
      width: 200,
      background: C.ink2,
      borderLeft: `1px solid ${C.line2}`,
      padding: "14px 12px",
      display: "flex", flexDirection: "column", gap: 10,
    }}>
      <div style={{ fontSize: 9, color: "#3A3828", letterSpacing: 1.5, fontFamily: "'DM Mono', monospace" }}>
        AGENT SELECTOR
      </div>

      {AGENTS.map(a => (
        <button key={a.id} onClick={() => onSelect(a.id)} style={{
          padding: "8px 10px",
          borderRadius: 9,
          border: `1px solid ${activeAgent === a.id ? a.color + "50" : C.line2}`,
          background: activeAgent === a.id ? a.color + "10" : "transparent",
          cursor: "pointer",
          textAlign: "right",
          transition: "all 0.15s",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
            {thinking && currentAgent === a.id && <Dot color={a.color} pulse />}
            <span style={{ fontSize: 11, color: activeAgent === a.id ? a.color : C.stone2 }}>
              {a.name}
            </span>
            <span style={{ fontSize: 14, color: a.color }}>{a.icon}</span>
          </div>
          <div style={{ fontSize: 9, color: "#3A3828", marginTop: 2, fontFamily: "'DM Mono', monospace" }}>
            {a.desc}
          </div>
        </button>
      ))}

      {thinking && (
        <div style={{
          marginTop: 8,
          padding: "10px",
          borderRadius: 9,
          background: C.golddim,
          border: `1px solid ${C.gold}30`,
        }}>
          <div style={{ fontSize: 9, color: C.gold, fontFamily: "'DM Mono', monospace", marginBottom: 6 }}>
            ACTIVE
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {["Intent ✅", "Graph ✅", "Execute 🔄"].map((s, i) => (
              <div key={i} style={{ fontSize: 10, color: C.stone2, fontFamily: "'DM Mono', monospace" }}>
                {s}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── MAIN APP ──────────────────────────────────────────────────────
export default function OneAgentOS() {
  const [messages, setMessages] = useState<any[]>([
    {
      id: 1,
      role: "assistant",
      content: "**مرحباً بك في Jnus.**\n\nاكتب هدفك وسأتولى الباقي — من الفهم والتخطيط حتى التنفيذ الكامل.",
      intent: null,
    }
  ]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [activeAgent, setActiveAgent] = useState("auto");
  const [activeConvo, setActiveConvo] = useState(1);
  const [conversations, setConversations] = useState(SAMPLE_CONVOS);
  const [stats, setStats] = useState({
    frameworks: 24,
    modules: 62,
    tests: 11,
    memory: 8,
    loading: true,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [agentsRes, metricsRes] = await Promise.allSettled([
          fetch(`${API_URL}/v1/agents`),
          fetch(`${API_URL}/metrics`),
        ]);

        const agents  = agentsRes.status  === "fulfilled" ? await agentsRes.value.json()  : null;
        const metrics = metricsRes.status === "fulfilled" ? await metricsRes.value.json() : null;

        setStats(prev => ({
          ...prev,
          frameworks: agents?.total              ?? prev.frameworks,
          memory:     metrics?.active_sessions   ?? prev.memory,
          loading: false,
        }));
      } catch {
        setStats(prev => ({ ...prev, loading: false }));
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 30_000);
    return () => clearInterval(interval);
  }, []);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || thinking) return;

    const userMsg = { id: Date.now(), role: "user", content: text };
    setMessages((prev: any[]) => [...prev, userMsg]);
    setInput("");
    setThinking(true);

    // Create assistant message placeholder
    const assistantId = Date.now() + 1;
    let sessionId = `session_${activeConvo}`;

    setMessages((prev: any[]) => [...prev, {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
      intent: null,
      agent: null,
      duration: null,
      cost: null,
      tokens: null,
    }]);

    try {
      // Stream from real API
      let fullContent = "";

      for await (const chunk of streamChat(text, sessionId)) {
        const { type, content } = chunk;

        switch (type) {
          case "token":
            fullContent += content;
            setMessages((prev: any[]) => prev.map((m: any) =>
              m.id === assistantId ? { ...m, content: fullContent } : m
            ));
            break;

          case "error":
            fullContent += `\n\n⚠️ ${content}`;
            setMessages((prev: any[]) => prev.map((m: any) =>
              m.id === assistantId ? { ...m, content: fullContent } : m
            ));
            break;
        }
      }

      // Mark as done
      setMessages((prev: any[]) => prev.map((m: any) =>
        m.id === assistantId ? { ...m, streaming: false } : m
      ));
    } catch (err: any) {
      // Fallback: if API is not available, show a friendly message
      setMessages((prev: any[]) => prev.map((m: any) =>
        m.id === assistantId ? {
          ...m,
          content: `**مرحباً بك في Jnus!**\n\nهذا وضع التجربة — لتشغيل النظام الكامل:\n\`\`\`bash\ndocker compose up\n\`\`\`\n\nبعدها أعد فتح هذه الصفحة وستعمل جميع الميزات.`,
          streaming: false,
        } : m
      ));
    }

    setThinking(false);
  }, [input, thinking, activeAgent, activeConvo]);


  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const newConversation = () => {
    const id = Date.now();
    setConversations((prev: any[]) => [{ id, title: "محادثة جديدة", intent: "CODE", time: "الآن" }, ...prev]);
    setActiveConvo(id);
    setMessages([{
      id: 1, role: "assistant",
      content: "محادثة جديدة. كيف يمكنني مساعدتك؟",
      intent: null,
    }]);
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
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.5; transform: scale(1.3); }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40%            { transform: translateY(-5px); }
        }
        button { outline: none; }
        textarea { outline: none; resize: none; }
      `}</style>

      <div style={{
        display: "flex",
        height: "100vh",
        fontFamily: "'Noto Kufi Arabic', sans-serif",
        background: C.paper,
        color: C.txt,
        direction: "rtl",
        overflow: "hidden",
      }}>
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          activeId={activeConvo}
          onSelect={setActiveConvo}
          onNew={newConversation}
        />

        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          
          {/* Header */}
          <div style={{
            padding: "12px 20px",
            borderBottom: `1px solid ${C.line}`,
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(245,243,239,.95)",
            backdropFilter: "blur(10px)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Dot color={C.green} pulse />
              <span style={{ fontSize: 11, color: C.muted, fontFamily: "'DM Mono', monospace" }}>
                جاهز للمساعدة
              </span>
            </div>

            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <span style={{
                fontSize: 9, color: C.green,
                padding: "2px 7px",
                background: C.green + "10",
                border: `1px solid ${C.green}25`,
                borderRadius: 4,
                fontFamily: "'DM Mono', monospace",
              }}>متصل ✓</span>
              <a href="/" style={{
                padding: "5px 12px",
                background: "transparent",
                border: `1px solid ${C.line}`,
                borderRadius: 6,
                fontSize: 10,
                color: C.muted,
                cursor: "pointer",
                fontFamily: "'DM Mono', monospace",
                textDecoration: "none",
                transition: "all 0.15s",
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.txt; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = C.line; e.currentTarget.style.color = C.muted; }}
              >
                ← رجوع
              </a>
            </div>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px 32px",
          }}>
            {messages.map((msg: any) => <Message key={msg.id} msg={msg} />)}
            {thinking && (
              <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 11,
                  background: C.ink, border: `1px solid ${C.line2}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, color: C.gold, fontFamily: "'Playfair Display', serif", fontWeight: 700,
                }}>J</div>
                <div style={{
                  padding: "12px 16px",
                  borderRadius: "4px 14px 14px 14px",
                  background: "#fff", border: `1px solid ${C.line}`,
                }}>
                  <TypingIndicator />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: "14px 20px 18px",
            borderTop: `1px solid ${C.line}`,
            background: "rgba(245,243,239,.97)",
          }}>
            {/* Agent pills */}
            <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
              {AGENTS.map(a => (
                <AgentBadge key={a.id} agent={a} active={activeAgent === a.id} onClick={() => setActiveAgent(a.id)} />
              ))}
            </div>

            {/* Input box */}
            <div style={{
              display: "flex", gap: 10, alignItems: "flex-end",
              padding: "10px 14px",
              borderRadius: 16,
              border: `1.5px solid ${input ? C.gold : C.line}`,
              background: "#fff",
              transition: "border-color 0.2s",
              boxShadow: input ? `0 2px 20px rgba(201,168,76,.15)` : "0 2px 12px rgba(0,0,0,.05)",
            }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="اكتب هدفك هنا... (Enter للإرسال)"
                rows={1}
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  color: C.txt,
                  fontSize: 13,
                  lineHeight: 1.6,
                  fontFamily: "'Noto Kufi Arabic', sans-serif",
                  maxHeight: 120,
                  overflowY: "auto",
                }}
                onInput={e => {
                  const target = e.currentTarget;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 120) + "px";
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || thinking}
                style={{
                  width: 36, height: 36,
                  borderRadius: 10,
                  border: "none",
                  background: input.trim() && !thinking ? C.ink : C.line,
                  color: input.trim() && !thinking ? C.gold : C.dim,
                  cursor: input.trim() && !thinking ? "pointer" : "not-allowed",
                  fontSize: 16,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0,
                  transition: "all 0.2s",
                }}
              >
                ↑
              </button>
            </div>

            <div style={{
              marginTop: 7,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ fontSize: 9, color: C.dim, fontFamily: "'DM Mono', monospace" }}>
                Shift+Enter للسطر الجديد
              </span>
              <span style={{ fontSize: 9, color: C.dim, fontFamily: "'DM Mono', monospace" }}>
                متوسط التكلفة أقل من $0.01
              </span>
            </div>
          </div>
        </div>

        {/* Agent Panel */}
        <AgentPanel
          activeAgent={activeAgent}
          onSelect={setActiveAgent}
          thinking={thinking}
          currentAgent={activeAgent}
        />
      </div>
    </>
  );
}
