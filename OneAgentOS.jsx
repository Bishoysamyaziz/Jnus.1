import { useState, useRef, useEffect, useCallback } from "react";

// ── PALETTE ──────────────────────────────────────────────────────
const T = {
  bg:          "#080810",
  bgDeep:      "#05050C",
  surface:     "#0F0F1A",
  surfaceHi:   "#161625",
  surfaceHover:"#1C1C2E",
  border:      "#1E1E35",
  borderHi:    "#2E2E50",
  accent:      "#7B6EF6",
  accentHi:    "#9D93FF",
  accentGlow:  "#7B6EF620",
  accentSoft:  "#C4BEFF",
  gold:        "#E8B96A",
  goldSoft:    "#F5D99A",
  teal:        "#3DD6C0",
  tealSoft:    "#A8F0E6",
  rose:        "#F06292",
  text:        "#E8E6F0",
  textMuted:   "#7A7890",
  textDim:     "#3A384A",
  green:       "#5DDC9A",
  amber:       "#F5A623",
};

// ── AGENT FRAMEWORKS ─────────────────────────────────────────────
const AGENTS = [
  { id: "auto",        name: "Auto",        icon: "◈", color: T.accent,  desc: "اختيار تلقائي" },
  { id: "crewai",      name: "CrewAI",       icon: "⬡", color: T.teal,   desc: "Multi-role" },
  { id: "autogen",     name: "AutoGen",      icon: "◉", color: T.gold,   desc: "Group chat" },
  { id: "metagpt",     name: "MetaGPT",      icon: "▣", color: T.rose,   desc: "Software Co." },
  { id: "langchain",   name: "LangChain",    icon: "⟁", color: T.accentHi, desc: "Chain of thought" },
  { id: "aider",       name: "Aider",        icon: "⌬", color: T.green,  desc: "Code editing" },
];

const INTENTS = [
  { type: "CODE",         label: "كود",       color: T.green,  icon: "⌨" },
  { type: "RESEARCH",     label: "بحث",       color: T.teal,   icon: "◎" },
  { type: "CREATIVE",     label: "إبداعي",    color: T.rose,   icon: "✦" },
  { type: "DATA",         label: "بيانات",    color: T.gold,   icon: "▦" },
  { type: "PLANNING",     label: "تخطيط",     color: T.accent, icon: "◈" },
  { type: "AUTOMATION",   label: "أتمتة",     color: T.amber,  icon: "⚡" },
];

const SAMPLE_CONVOS = [
  { id: 1, title: "بناء REST API للـ authentication", intent: "CODE",     time: "منذ ساعتين" },
  { id: 2, title: "تحليل بيانات المبيعات Q1",          intent: "DATA",     time: "أمس" },
  { id: 3, title: "خطة تسويق لمنتج SaaS",              intent: "PLANNING", time: "منذ يومين" },
];

// ── MOCK STREAMING RESPONSE ───────────────────────────────────────
const MOCK_RESPONSES = {
  default: `سأبدأ تحليل طلبك الآن.

\`\`\`python
# OneAgent — تنفيذ المهمة
async def execute_task(goal: str) -> Result:
    intent = await classifier.classify(goal)
    graph = await planner.build(intent)
    
    async for result in orchestrator.stream(graph):
        yield result
\`\`\`

النظام حدد النية بدقة **97%** واختار أنسب الـ frameworks للتنفيذ.

**الخطوات:**
1. ✅ تحليل النية — CODE intent
2. ✅ بناء Task Graph — 3 مهام متوازية  
3. 🔄 تنفيذ Aider agent...
4. ⏳ مراجعة النتائج

الوقت المتوقع: **~8 ثوانٍ**`,
};

// ── COMPONENTS ────────────────────────────────────────────────────

function Dot({ color, pulse }) {
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

function AgentBadge({ agent, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 6,
      padding: "5px 10px",
      borderRadius: 8,
      border: `1px solid ${active ? agent.color + "60" : T.border}`,
      background: active ? agent.color + "12" : "transparent",
      cursor: "pointer",
      transition: "all 0.15s ease",
    }}>
      <span style={{ fontSize: 13, color: agent.color }}>{agent.icon}</span>
      <span style={{ fontSize: 11, color: active ? agent.color : T.textMuted, fontFamily: "'DM Mono', monospace" }}>
        {agent.name}
      </span>
    </button>
  );
}

function IntentTag({ intent }) {
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
          background: T.accent,
          opacity: 0.7,
          animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

function MessageContent({ content, streaming }) {
  const lines = content.split("\n");
  const rendered = [];
  let inCode = false;
  let codeLines = [];
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
            border: `1px solid ${T.border}`,
          }}>
            {codeLang && (
              <div style={{
                padding: "6px 14px",
                background: T.surface,
                borderBottom: `1px solid ${T.border}`,
                fontSize: 10,
                color: T.textMuted,
                fontFamily: "'DM Mono', monospace",
                display: "flex", justifyContent: "space-between",
              }}>
                <span>{codeLang}</span>
                <span style={{ color: T.green, letterSpacing: 0.5 }}>● LIVE</span>
              </div>
            )}
            <pre style={{
              margin: 0, padding: "14px",
              background: T.bgDeep,
              fontSize: 12,
              lineHeight: 1.7,
              color: T.tealSoft,
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
        <strong key={i} style={{ color: T.accentSoft, display: "block", margin: "6px 0 2px" }}>
          {line.slice(2, -2)}
        </strong>
      );
    } else if (line.match(/^\d\./)) {
      rendered.push(
        <div key={i} style={{ display: "flex", gap: 8, margin: "3px 0", fontSize: 13, color: T.text }}>
          <span style={{ color: T.accent, fontFamily: "'DM Mono', monospace", minWidth: 16 }}>
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
        <span key={i} style={{ fontSize: 13, lineHeight: 1.8, color: T.text, display: "block" }}>
          {parts.map((p, j) => j % 2 === 0
            ? <span key={j}>{p}</span>
            : <strong key={j} style={{ color: T.accentSoft }}>{p}</strong>
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

function Message({ msg }) {
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
        borderRadius: isUser ? 10 : 12,
        background: isUser ? T.accent + "20" : T.surface,
        border: `1px solid ${isUser ? T.accent + "40" : T.border}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 13,
        flexShrink: 0,
        color: isUser ? T.accent : T.accentHi,
      }}>
        {isUser ? "أ" : "◈"}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: "78%", minWidth: 60 }}>
        {!isUser && msg.intent && (
          <div style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <IntentTag intent={msg.intent} />
            {msg.agent && (
              <span style={{
                fontSize: 10, color: T.textMuted,
                fontFamily: "'DM Mono', monospace",
              }}>via {msg.agent}</span>
            )}
            {msg.duration && (
              <span style={{ fontSize: 10, color: T.textDim, fontFamily: "'DM Mono', monospace" }}>
                {msg.duration}
              </span>
            )}
          </div>
        )}
        <div style={{
          padding: isUser ? "10px 14px" : "12px 16px",
          borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
          background: isUser ? T.accent + "18" : T.surface,
          border: `1px solid ${isUser ? T.accent + "35" : T.border}`,
          fontSize: 13,
          lineHeight: 1.7,
          color: T.text,
        }}>
          {isUser
            ? <span>{msg.content}</span>
            : <MessageContent content={msg.content} streaming={msg.streaming} />
          }
        </div>
        {!isUser && msg.cost && (
          <div style={{ marginTop: 5, display: "flex", gap: 10 }}>
            <span style={{ fontSize: 10, color: T.textDim, fontFamily: "'DM Mono', monospace" }}>
              ${msg.cost} · {msg.tokens} tokens
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function Sidebar({ conversations, activeId, onSelect, onNew }) {
  return (
    <div style={{
      width: 240,
      background: T.bgDeep,
      borderRight: `1px solid ${T.border}`,
      display: "flex", flexDirection: "column",
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{
        padding: "18px 16px 14px",
        borderBottom: `1px solid ${T.border}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 28, height: 28,
            borderRadius: 9,
            background: `linear-gradient(135deg, ${T.accent}, ${T.teal})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 13,
          }}>◈</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: T.text, letterSpacing: -0.3 }}>
              OneAgent
            </div>
            <div style={{ fontSize: 9, color: T.textMuted, fontFamily: "'DM Mono', monospace", letterSpacing: 1 }}>
              OS v1.0
            </div>
          </div>
        </div>
      </div>

      {/* New Chat */}
      <div style={{ padding: "10px 10px 6px" }}>
        <button onClick={onNew} style={{
          width: "100%",
          padding: "8px 12px",
          borderRadius: 9,
          border: `1px dashed ${T.borderHi}`,
          background: "transparent",
          color: T.textMuted,
          fontSize: 12,
          cursor: "pointer",
          display: "flex", alignItems: "center", gap: 6,
          transition: "all 0.15s",
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent + "60"; e.currentTarget.style.color = T.accent; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = T.borderHi; e.currentTarget.style.color = T.textMuted; }}
        >
          <span style={{ fontSize: 16, lineHeight: 1 }}>+</span>
          محادثة جديدة
        </button>
      </div>

      {/* History */}
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 10px" }}>
        <div style={{ fontSize: 9, color: T.textDim, letterSpacing: 1.5, padding: "8px 6px 4px", fontFamily: "'DM Mono', monospace" }}>
          RECENT
        </div>
        {conversations.map(c => (
          <button key={c.id} onClick={() => onSelect(c.id)} style={{
            width: "100%", textAlign: "right",
            padding: "8px 8px",
            borderRadius: 8,
            border: "1px solid transparent",
            background: activeId === c.id ? T.surfaceHi : "transparent",
            cursor: "pointer",
            marginBottom: 2,
            transition: "all 0.12s",
          }}
            onMouseEnter={e => { if (activeId !== c.id) e.currentTarget.style.background = T.surfaceHover; }}
            onMouseLeave={e => { if (activeId !== c.id) e.currentTarget.style.background = "transparent"; }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
              <IntentTag intent={c.intent} />
            </div>
            <div style={{ fontSize: 11, color: activeId === c.id ? T.text : T.textMuted, marginTop: 4, lineHeight: 1.4, textAlign: "right" }}>
              {c.title}
            </div>
            <div style={{ fontSize: 9, color: T.textDim, marginTop: 3, fontFamily: "'DM Mono', monospace" }}>
              {c.time}
            </div>
          </button>
        ))}
      </div>

      {/* Footer stats */}
      <div style={{
        padding: "10px 14px",
        borderTop: `1px solid ${T.border}`,
        display: "flex", flexDirection: "column", gap: 5,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 9, color: T.textDim, fontFamily: "'DM Mono', monospace" }}>اليوم</span>
          <span style={{ fontSize: 9, color: T.green, fontFamily: "'DM Mono', monospace" }}>$0.003</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 9, color: T.textDim, fontFamily: "'DM Mono', monospace" }}>MODEL</span>
          <span style={{ fontSize: 9, color: T.accent, fontFamily: "'DM Mono', monospace" }}>claude-s4</span>
        </div>
      </div>
    </div>
  );
}

function AgentPanel({ activeAgent, onSelect, thinking, currentAgent }) {
  return (
    <div style={{
      width: 200,
      background: T.bgDeep,
      borderLeft: `1px solid ${T.border}`,
      padding: "14px 12px",
      display: "flex", flexDirection: "column", gap: 10,
    }}>
      <div style={{ fontSize: 9, color: T.textDim, letterSpacing: 1.5, fontFamily: "'DM Mono', monospace" }}>
        AGENT SELECTOR
      </div>

      {AGENTS.map(a => (
        <button key={a.id} onClick={() => onSelect(a.id)} style={{
          padding: "8px 10px",
          borderRadius: 9,
          border: `1px solid ${activeAgent === a.id ? a.color + "50" : T.border}`,
          background: activeAgent === a.id ? a.color + "10" : "transparent",
          cursor: "pointer",
          textAlign: "right",
          transition: "all 0.15s",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
            {thinking && currentAgent === a.id && <Dot color={a.color} pulse />}
            <span style={{ fontSize: 11, color: activeAgent === a.id ? a.color : T.textMuted }}>
              {a.name}
            </span>
            <span style={{ fontSize: 14, color: a.color }}>{a.icon}</span>
          </div>
          <div style={{ fontSize: 9, color: T.textDim, marginTop: 2, fontFamily: "'DM Mono', monospace" }}>
            {a.desc}
          </div>
        </button>
      ))}

      {thinking && (
        <div style={{
          marginTop: 8,
          padding: "10px",
          borderRadius: 9,
          background: T.accent + "08",
          border: `1px solid ${T.accent}20`,
        }}>
          <div style={{ fontSize: 9, color: T.accent, fontFamily: "'DM Mono', monospace", marginBottom: 6 }}>
            ACTIVE
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {["Intent ✅", "Graph ✅", "Execute 🔄"].map((s, i) => (
              <div key={i} style={{ fontSize: 10, color: T.textMuted, fontFamily: "'DM Mono', monospace" }}>
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
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: "مرحباً. أنا OneAgent OS — نظام يوحّد 24 AI framework في واجهة واحدة.\n\nاكتب هدفك بالعربية أو الإنجليزية وسأختار أنسب framework تلقائياً.",
      intent: null,
    }
  ]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [activeAgent, setActiveAgent] = useState("auto");
  const [activeConvo, setActiveConvo] = useState(1);
  const [conversations, setConversations] = useState(SAMPLE_CONVOS);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const simulateStream = useCallback(async (text, msgId) => {
    const words = text.split(" ");
    let current = "";
    for (let i = 0; i < words.length; i++) {
      current += (i > 0 ? " " : "") + words[i];
      setMessages(prev => prev.map(m =>
        m.id === msgId ? { ...m, content: current, streaming: i < words.length - 1 } : m
      ));
      await new Promise(r => setTimeout(r, 18 + Math.random() * 25));
    }
  }, []);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || thinking) return;

    const userMsg = { id: Date.now(), role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setThinking(true);

    // Detect intent
    const intentMap = {
      كود: "CODE", code: "CODE", api: "CODE", function: "CODE",
      بحث: "RESEARCH", search: "RESEARCH", ابحث: "RESEARCH",
      بيانات: "DATA", data: "DATA", تحليل: "DATA",
      خطة: "PLANNING", plan: "PLANNING", خطط: "PLANNING",
      اتمتة: "AUTOMATION", automate: "AUTOMATION",
    };
    const lowerText = text.toLowerCase();
    let detectedIntent = "CODE";
    for (const [key, val] of Object.entries(intentMap)) {
      if (lowerText.includes(key)) { detectedIntent = val; break; }
    }

    const agentMap = {
      CODE: "Aider",
      RESEARCH: "LangChain",
      DATA: "TaskWeaver",
      PLANNING: "CrewAI",
      AUTOMATION: "SuperAGI",
    };

    await new Promise(r => setTimeout(r, 900 + Math.random() * 600));

    const assistantId = Date.now() + 1;
    const duration = (1.2 + Math.random() * 2.8).toFixed(1) + "s";
    const cost = (0.001 + Math.random() * 0.008).toFixed(4);
    const tokens = Math.floor(200 + Math.random() * 800);

    setMessages(prev => [...prev, {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
      intent: detectedIntent,
      agent: activeAgent === "auto" ? agentMap[detectedIntent] : AGENTS.find(a => a.id === activeAgent)?.name,
      duration,
      cost,
      tokens,
    }]);

    setThinking(false);
    await simulateStream(MOCK_RESPONSES.default, assistantId);
  }, [input, thinking, activeAgent, simulateStream]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const newConversation = () => {
    const id = Date.now();
    setConversations(prev => [{ id, title: "محادثة جديدة", intent: "CODE", time: "الآن" }, ...prev]);
    setActiveConvo(id);
    setMessages([{
      id: 1, role: "assistant",
      content: "محادثة جديدة. ما هدفك؟",
      intent: null,
    }]);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${T.bg}; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${T.borderHi}; border-radius: 2px; }
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
        @keyframes shimmer {
          0%   { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        button { outline: none; }
        textarea { outline: none; resize: none; }
      `}</style>

      <div style={{
        display: "flex",
        height: "100vh",
        fontFamily: "'IBM Plex Sans Arabic', sans-serif",
        background: T.bg,
        color: T.text,
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
            borderBottom: `1px solid ${T.border}`,
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: T.bgDeep,
            backdropFilter: "blur(10px)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Dot color={T.green} pulse />
              <span style={{ fontSize: 11, color: T.textMuted, fontFamily: "'DM Mono', monospace" }}>
                24 frameworks · online
              </span>
            </div>

            <div style={{ display: "flex", gap: 6 }}>
              {["Redis ✓", "Postgres ✓", "Qdrant ✓"].map((s, i) => (
                <span key={i} style={{
                  fontSize: 9, color: T.green,
                  padding: "2px 7px",
                  background: T.green + "10",
                  border: `1px solid ${T.green}25`,
                  borderRadius: 4,
                  fontFamily: "'DM Mono', monospace",
                }}>{s}</span>
              ))}
            </div>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px 32px",
          }}>
            {messages.map(msg => <Message key={msg.id} msg={msg} />)}
            {thinking && (
              <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 12,
                  background: T.surface, border: `1px solid ${T.border}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, color: T.accentHi,
                }}>◈</div>
                <div style={{
                  padding: "12px 16px",
                  borderRadius: "4px 14px 14px 14px",
                  background: T.surface, border: `1px solid ${T.border}`,
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
            borderTop: `1px solid ${T.border}`,
            background: T.bgDeep,
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
              borderRadius: 14,
              border: `1px solid ${input ? T.accent + "50" : T.border}`,
              background: T.surface,
              transition: "border-color 0.2s",
            }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="اكتب هدفك... (Enter للإرسال)"
                rows={1}
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  color: T.text,
                  fontSize: 13,
                  lineHeight: 1.6,
                  fontFamily: "'IBM Plex Sans Arabic', sans-serif",
                  maxHeight: 120,
                  overflowY: "auto",
                }}
                onInput={e => {
                  e.target.style.height = "auto";
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || thinking}
                style={{
                  width: 34, height: 34,
                  borderRadius: 10,
                  border: "none",
                  background: input.trim() && !thinking
                    ? `linear-gradient(135deg, ${T.accent}, ${T.teal})`
                    : T.borderHi,
                  color: input.trim() && !thinking ? "white" : T.textDim,
                  cursor: input.trim() && !thinking ? "pointer" : "not-allowed",
                  fontSize: 15,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0,
                  transition: "all 0.2s",
                  transform: input.trim() && !thinking ? "scale(1)" : "scale(0.95)",
                }}
              >
                ↑
              </button>
            </div>

            <div style={{
              marginTop: 7,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ fontSize: 9, color: T.textDim, fontFamily: "'DM Mono', monospace" }}>
                Shift+Enter للسطر الجديد
              </span>
              <span style={{ fontSize: 9, color: T.textDim, fontFamily: "'DM Mono', monospace" }}>
                avg cost &lt; $0.01/req
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
