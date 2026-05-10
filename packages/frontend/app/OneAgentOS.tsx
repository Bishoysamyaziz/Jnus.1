"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";

// ─── Types ───────────────────────────────────────────────────
type IntentType = "CODE" | "RESEARCH" | "DATA" | "PLANNING" | "CONVERSATION" | "CREATIVE" | "AUTOMATION";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  metadata?: {
    intent?: IntentType;
    framework?: string;
    duration_ms?: number;
    tokens_used?: number;
  };
}

interface AgentInfo {
  name: string;
  class: string;
}

interface HealthStatus {
  status: string;
  version: string;
  agents: number;
  memory: { short_term: number; long_term: number; skill: number };
}

// ─── Constants ───────────────────────────────────────────────
const INTENTS: IntentType[] = ["CODE", "RESEARCH", "DATA", "PLANNING", "CONVERSATION", "CREATIVE", "AUTOMATION"];

const INTENT_EMOJIS: Record<IntentType, string> = {
  CODE: "💻",
  RESEARCH: "🔬",
  DATA: "📊",
  PLANNING: "📋",
  CONVERSATION: "💬",
  CREATIVE: "🎨",
  AUTOMATION: "⚡",
};

const INTENT_COLORS: Record<IntentType, string> = {
  CODE: "#3b82f6",
  RESEARCH: "#8b5cf6",
  DATA: "#10b981",
  PLANNING: "#f59e0b",
  CONVERSATION: "#ec4899",
  CREATIVE: "#f97316",
  AUTOMATION: "#ef4444",
};

// ─── Components ──────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-4 py-3">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span className="text-sm text-gray-400">Agent thinking...</span>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-gray-800/50 text-gray-400 text-xs px-3 py-1 rounded-full border border-gray-700/50">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-gray-800/80 text-gray-100 rounded-bl-md border border-gray-700/50"
        }`}
      >
        {!isUser && message.metadata?.intent && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-700/50">
            <span className="text-lg">{INTENT_EMOJIS[message.metadata.intent]}</span>
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: `${INTENT_COLORS[message.metadata.intent]}20`,
                color: INTENT_COLORS[message.metadata.intent],
              }}
            >
              {message.metadata.intent}
            </span>
            {message.metadata.framework && (
              <span className="text-xs text-gray-400">via {message.metadata.framework}</span>
            )}
          </div>
        )}
        <div className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</div>
        {message.metadata?.duration_ms && (
          <div className="mt-2 text-[10px] text-gray-500 flex gap-3">
            <span>⏱ {message.metadata.duration_ms}ms</span>
            {message.metadata.tokens_used && <span>🔤 {message.metadata.tokens_used} tokens</span>}
          </div>
        )}
      </div>
    </div>
  );
}

function IntentSelector({
  selected,
  onSelect,
}: {
  selected: IntentType;
  onSelect: (intent: IntentType) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {INTENTS.map((intent) => (
        <button
          key={intent}
          onClick={() => onSelect(intent)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
            selected === intent
              ? "ring-2 ring-offset-2 ring-offset-gray-900 scale-105"
              : "opacity-60 hover:opacity-100"
          }`}
          style={{
            backgroundColor: `${INTENT_COLORS[intent]}20`,
            color: INTENT_COLORS[intent],
            ...(selected === intent ? { ringColor: INTENT_COLORS[intent] } : {}),
          }}
        >
          <span>{INTENT_EMOJIS[intent]}</span>
          <span>{intent}</span>
        </button>
      ))}
    </div>
  );
}

function AgentGrid({ agents }: { agents: AgentInfo[] }) {
  return (
    <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
      {agents.map((agent) => (
        <div
          key={agent.name}
          className="bg-gray-800/50 rounded-lg p-2 text-center border border-gray-700/30 hover:border-blue-500/50 transition-colors"
        >
          <div className="text-lg mb-1">
            {agent.name === "crewai" ? "🤖" :
             agent.name === "autogen" ? "🔄" :
             agent.name === "langchain" ? "⛓️" :
             agent.name === "babyagi" ? "🧠" :
             agent.name === "swarm" ? "🐝" :
             agent.name === "aider" ? "👨‍💻" :
             agent.name === "openhands" ? "✋" :
             agent.name === "rasa" ? "🗣️" :
             agent.name === "autogpt" ? "🤯" :
             agent.name === "camel" ? "🐪" :
             agent.name === "metagpt" ? "🧙" :
             agent.name === "letta" ? "💭" :
             agent.name === "mem0" ? "🧩" :
             agent.name === "huggingface" ? "🤗" :
             agent.name === "haystack" ? "🧵" :
             agent.name === "llamaindex" ? "🦙" :
             agent.name === "semantic_kernel" ? "🌐" :
             agent.name === "taskweaver" ? "🕸️" :
             agent.name === "agentverse" ? "🌌" :
             agent.name === "agentgpt" ? "🤖" :
             agent.name === "botpress" ? "🤵" :
             agent.name === "superagi" ? "🦸" :
             agent.name === "langgraph" ? "🔀" :
             agent.name === "smolagents" ? "📦" : "⚙️"}
          </div>
          <div className="text-[10px] text-gray-400 truncate">{agent.name}</div>
        </div>
      ))}
    </div>
  );
}

function HealthPanel({ health }: { health: HealthStatus | null }) {
  if (!health) return null;
  return (
    <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">🩺 System Health</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className={`text-2xl ${health.status === "healthy" ? "text-green-400" : "text-yellow-400"}`}>
            {health.status === "healthy" ? "✅" : "⚠️"}
          </div>
          <div className="text-xs text-gray-400 mt-1">{health.status}</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-2xl text-blue-400">v{health.version}</div>
          <div className="text-xs text-gray-400 mt-1">Version</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-2xl text-purple-400">{health.agents}</div>
          <div className="text-xs text-gray-400 mt-1">Agents</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-2xl text-emerald-400">{health.memory.short_term + health.memory.long_term + health.memory.skill}</div>
          <div className="text-xs text-gray-400 mt-1">Memory Items</div>
        </div>
      </div>
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────

export default function OneAgentOS() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "system",
      content: "🧠 OneAgent OS ready — 24 agent frameworks loaded. How can I help you?",
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [selectedIntent, setSelectedIntent] = useState<IntentType>("CODE");
  const [isLoading, setIsLoading] = useState(false);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [showAgents, setShowAgents] = useState(false);
  const [showHealth, setShowHealth] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch agents on mount
  useEffect(() => {
    fetch("/api/agents")
      .then((r) => r.json())
      .then(setAgents)
      .catch(() => {});
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => {});
  }, []);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const startTime = performance.now();
      const response = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: userMessage.content,
          intent_type: selectedIntent,
          user_id: "web-ui",
          session_id: `web-${Date.now()}`,
        }),
      });
      const data = await response.json();
      const duration = Math.round(performance.now() - startTime);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.content || data.error || "No response",
        timestamp: Date.now(),
        metadata: {
          intent: selectedIntent,
          framework: data.framework,
          duration_ms: duration,
          tokens_used: data.tokens_used,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `❌ Error: ${error instanceof Error ? error.message : "Connection failed"}`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, selectedIntent]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-950 to-black text-white">
      {/* Header */}
      <header className="border-b border-gray-800/50 bg-gray-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-lg font-bold shadow-lg shadow-blue-500/20">
              OA
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                OneAgent OS
              </h1>
              <p className="text-[10px] text-gray-500">24 Agent Frameworks • Unified Orchestration</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAgents(!showAgents)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showAgents ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              🤖 Agents
            </button>
            <button
              onClick={() => setShowHealth(!showHealth)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showHealth ? "bg-emerald-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              🩺 Health
            </button>
          </div>
        </div>
      </header>

      {/* Panels */}
      {showAgents && (
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="bg-gray-900/50 backdrop-blur-xl rounded-xl p-4 border border-gray-800/50">
            <h2 className="text-sm font-semibold text-gray-300 mb-3">🤖 24 Agent Frameworks</h2>
            <AgentGrid agents={agents} />
          </div>
        </div>
      )}

      {showHealth && (
        <div className="max-w-6xl mx-auto px-4 py-4">
          <HealthPanel health={health} />
        </div>
      )}

      {/* Chat Area */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <IntentSelector selected={selectedIntent} onSelect={setSelectedIntent} />

        <div className="bg-gray-900/30 backdrop-blur-xl rounded-2xl border border-gray-800/50 min-h-[400px] max-h-[600px] overflow-y-auto p-4 mb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your task... (Shift+Enter for new line)"
              rows={1}
              className="w-full bg-gray-800/80 border border-gray-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 resize-none transition-all"
              style={{ minHeight: "44px", maxHeight: "120px" }}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none"
          >
            {isLoading ? "⏳" : "Send →"}
          </button>
        </div>

        {/* Quick actions */}
        <div className="flex gap-2 mt-4 flex-wrap">
          {[
            { label: "Write a Python function", intent: "CODE" as IntentType },
            { label: "Research AI trends", intent: "RESEARCH" as IntentType },
            { label: "Analyze data", intent: "DATA" as IntentType },
            { label: "Plan a project", intent: "PLANNING" as IntentType },
            { label: "Chat", intent: "CONVERSATION" as IntentType },
          ].map((action) => (
            <button
              key={action.label}
              onClick={() => {
                setInput(action.label);
                setSelectedIntent(action.intent);
                inputRef.current?.focus();
              }}
              className="text-xs px-3 py-1.5 bg-gray-800/50 hover:bg-gray-700/50 text-gray-400 hover:text-gray-200 rounded-lg border border-gray-700/30 transition-all"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-4 text-center">
        <p className="text-xs text-gray-600">
          OneAgent OS v1.0 • 24 Agent Frameworks • Built with ❤️
        </p>
      </footer>
    </div>
  );
}
