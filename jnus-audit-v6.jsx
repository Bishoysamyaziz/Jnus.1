import { useState } from "react";

const C = {
  bg:"#0D0D14", surface:"#13131F", surfaceHi:"#1A1A2E",
  border:"#2A2A45", borderHi:"#3D3D65",
  purple:"#B57BFF", purpleDeep:"#7C3AED", purpleSoft:"#C4B5FD", lavender:"#E8E0FF",
  red:"#F87171", redSoft:"#FCA5A5", redBg:"#150808",
  amber:"#FBBF24", amberSoft:"#FDE68A", amberBg:"#15110A",
  green:"#4ADE80", greenSoft:"#86EFAC", greenBg:"#081508",
  blue:"#60A5FA", blueSoft:"#BFDBFE", blueBg:"#080F18",
  teal:"#2DD4BF", tealSoft:"#99F6E4",
  orange:"#F97316", orangeSoft:"#FED7AA",
  text:"#E8E0FF", textMuted:"#8B7FC7", textDim:"#4A4470",
};

// ─── DATA ────────────────────────────────────────────────────────

const SUMMARY = {
  totalFiles: 107,
  pythonFiles: 47,
  tsxFiles: 6,
  testFiles: 21,
  frameworks: 24,
  agentFiles: 24,
  criticalBugs: 5,
  regularBugs: 8,
  missing: 9,
  newInV6: 3,
  fixedInV6: 0,
};

const WHATS_NEW = [
  {
    title: "OpenAI-Compatible API Endpoint ✓",
    file: "packages/api/main.py",
    color: C.green,
    icon: "⬡",
    detail: "أُضيف /v1/chat/completions بتنسيق OpenAI الكامل. الآن أي client يدعم OpenAI SDK يشتغل مع النظام مباشرة. SSE streaming بـ [DONE] signal صح.",
    quality: "ممتاز",
  },
  {
    title: "Frontend مكتمل مع SSE Streaming حقيقي ✓",
    file: "packages/frontend/app/OneAgentOS.tsx",
    color: C.green,
    icon: "◈",
    detail: "الـ Frontend أُعيد كتابته بالكامل: 868 سطر. فيه real fetch لـ /v1/chat/completions مع SSE parsing, 25 agent selector, RTL Arabic UI, auto-resize textarea, code block renderer, typing indicator.",
    quality: "ممتاز",
  },
  {
    title: "Chat Route /chat ✓",
    file: "packages/frontend/app/chat/page.tsx",
    color: C.teal,
    icon: "◎",
    detail: "صفحة /chat منفصلة أُضيفت. بسيطة جداً — بس تسمح بـ deep-link للـ chat مباشرة.",
    quality: "بسيط",
  },
];

const CRITICAL_BUGS = [
  {
    id:"C1", file:"requirements.txt",
    title:"10 حزم pip بأسماء خاطئة أو غير موجودة — pip install هيفشل",
    status:"لم تُصلح",
    body:"نفس المشكلة من v5. كل pip install سيفشل بسبب 10 package names غلط.",
    detail:`❌ babyagi==0.1.0   → غير موجود على PyPI
❌ swarm==0.1.0     → يجب: openai-swarm (from GitHub)
❌ openhands==0.1.0 → يجب: openhands-ai
❌ agentgpt==0.2.0  → غير قابل للـ pip install
❌ botpress==1.0.0  → ليس Python package
❌ superagi==0.0.5  → version غير موجودة
❌ taskweaver==0.1.0→ from GitHub فقط
❌ autogpt==0.5.0   → from GitHub فقط
❌ agentverse==0.2.0→ version خاطئة
❌ camel-ai==0.2.12 → تحقق من version`,
    fix:`# الحل: اعمل ملف install_frameworks.sh
pip install openai-swarm openhands-ai camel-ai
# و GitHub installs:
pip install git+https://github.com/microsoft/TaskWeaver
pip install git+https://github.com/Significant-Gravitas/AutoGPT
# + extras_require في pyproject.toml`,
  },
  {
    id:"C2", file:"packages/api/main.py + packages/api/auth.py",
    title:"Authentication مكسور — get_user_manager=lambda: None",
    status:"لم تُصلح",
    body:"نفس المشكلة. FastAPIUsers بدون User model ولا database. أي /auth request سيسبب TypeError.",
    detail:`# السطر المكسور (لم يتغير):
fastapi_users = FastAPIUsers(
    get_user_manager=lambda: None,  # ← CRASH
    auth_backends=[auth_backend],
)
# المشكلة: لا User model، لا SQLAlchemy table
# لا get_user_manager function حقيقية`,
    fix:`# الحل الكامل:
from fastapi_users.db import SQLAlchemyUserDatabase
class User(SQLAlchemyBaseUserTableUUID, Base): pass

async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers(get_user_manager, [auth_backend])`,
  },
  {
    id:"C3", file:"packages/api/main.py",
    title:"CORS مكسور — allow_origins=['*'] مع credentials=True",
    status:"لم تُصلح",
    body:"نفس الخطأ. المتصفح سيرفض كل الطلبات المعتمدة وفق مواصفات CORS.",
    detail:`# مكسور (لم يتغير):
CORSMiddleware(
    allow_origins=["*"],      # ← INVALID مع credentials
    allow_credentials=True,   # ← browsers ترفض
)
# NOTE: الـ v1/chat/completions الجديد
# سيواجه نفس المشكلة من الـ browser`,
    fix:`CORSMiddleware(
    allow_origins=["http://localhost:3000",
                   "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET","POST","DELETE"],
    allow_headers=["Authorization","Content-Type"],
)`,
  },
  {
    id:"C4", file:"packages/core/orchestrator.py",
    title:"os.environ mutation داخل async — Race Condition مؤكد",
    status:"لم تُصلح",
    body:"نفس المشكلة. تعديل env vars أثناء async execution يؤثر على كل الـ workers بالتوازي.",
    detail:`# خطر — لم يتغير:
os.environ["OPENAI_BASE_URL"] = selected_tier["base_url"]
os.environ["OPENAI_API_KEY"]  = selected_tier["api_key"]
os.environ["DEFAULT_MODEL"]   = selected_tier["models"][0]

# الآن مع الـ /v1/chat/completions الجديد
# طلبان متزامنان = race condition أكبر`,
    fix:`# مرر config كـ parameter مباشرة:
llm_config = {
    "base_url": tier["base_url"],
    "api_key":  tier["api_key"],
    "model":    tier["models"][0],
}
await agent.execute(task, memory, llm_config=llm_config)`,
  },
  {
    id:"C5", file:"packages/core/memory/skill_memory.py",
    title:"SHA256 كـ Embedding — Semantic Search معطل تماماً",
    status:"لم تُصلح",
    body:"نفس المشكلة. Skill Memory لا تعمل كـ vector search لأن SHA256 لا يعبر عن المعنى.",
    detail:`# مش embedding — ده hash:
def _simple_embed(self, text):
    hash_bytes = hashlib.sha256(text.encode()).digest()
    # "coding" و "programming" → cosine ≈ random
    # لا توجد علاقة دلالية بين الـ vectors`,
    fix:`# استخدم FastEmbed (مجاني، بدون GPU):
from fastembed import TextEmbedding
model = TextEmbedding("BAAI/bge-small-en-v1.5")  # 384-dim

def embed(self, text: str) -> list[float]:
    return list(model.embed([text]))[0].tolist()`,
  },
];

const BUGS_V6 = [
  {
    id:"B1", sev:"جديد في v6", file:"packages/frontend/app/OneAgentOS.tsx",
    title:"API_URL و API_BASE متعارضان — تعريف مزدوج",
    body:`السطر 6: const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
السطر 75: const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
اثنان بنفس القيمة. الـ stats fetch يستخدم API_URL والـ streamChat يستخدم API_BASE.`,
    fix:"احذف أحدهما واستخدم الآخر في كل مكان.",
    color: C.amber,
  },
  {
    id:"B2", sev:"جديد في v6", file:"packages/frontend/app/OneAgentOS.tsx",
    title:"الـ activeAgent المختار لا يُرسل للـ Backend",
    body:`المستخدم يختار agent (مثلاً CrewAI) لكن streamChat() لا يرسله:
body: JSON.stringify({ model: "claude-s4", messages: [...], stream: true })
مفيش "agent" أو "preferred_agent" في الـ request body.`,
    fix:`أضف للـ request body:
agent_preference: activeAgent !== "auto" ? activeAgent : undefined`,
    color: C.amber,
  },
  {
    id:"B3", sev:"جديد في v6", file:"packages/frontend/app/OneAgentOS.tsx",
    title:"Status 'متصل ✓' ثابت — لا يعكس حالة الـ API الحقيقية",
    body:"الـ header دايماً يعرض 'متصل ✓' حتى لو الـ API down. الـ stats fetch يفشل بـ silence.",
    fix:`const [apiOnline, setApiOnline] = useState(false);
// في fetchStats: setApiOnline(true) عند نجاح، setApiOnline(false) عند فشل`,
    color: C.amber,
  },
  {
    id:"B4", sev:"جديد في v6", file:"packages/api/main.py",
    title:"openai_event_generator يبعت كل status كـ content — يلوث الـ response",
    body:`كل status update يتحول لـ content:
"⏳ تحليل النية..."  "⏳ بناء خريطة المهام..."
هذا يظهر للمستخدم كجزء من الرد الأصلي.`,
    fix:`أضف type field في الـ metadata:
# أو فلتر الـ status chunks من الـ /v1/chat/completions
# واعرضهم فقط في /v1/chat الأصلي`,
    color: C.amber,
  },
  {
    id:"B5", sev:"موروث", file:"packages/core/base_agent.py",
    title:"AgentRegistry فارغ دايماً — لا registration عند الـ startup",
    body:"الـ 24 agent مكتوبين لكن مش متسجلين. الـ Orchestrator دايماً يقع على _simulate_agent_response.",
    fix:"أضف AgentRegistry.register() في lifespan() لكل agent.",
    color: C.red,
  },
  {
    id:"B6", sev:"موروث", file:"packages/core/memory/long_term.py",
    title:"PostgreSQL URL format خاطئ لـ asyncpg",
    body:"asyncpg يحتاج postgresql+asyncpg:// وليس postgresql://.",
    fix:`url = url.replace("postgresql://", "postgresql+asyncpg://")`,
    color: C.red,
  },
  {
    id:"B7", sev:"موروث", file:"packages/core/tools/web_search.py",
    title:"Web Search يرجع بيانات وهمية (placeholder)",
    body:"كل search ترجع 'simulated result'. لا اتصال حقيقي بأي search engine.",
    fix:"ادمج DuckDuckGo API (مجاني) أو Serper API.",
    color: C.amber,
  },
  {
    id:"B8", sev:"موروث", file:"packages/core/tools/code_executor.py",
    title:"Code Executor يستخدم exec() بدون sandbox",
    body:"exec() في Python namespace لا يعزل الكود. أي agent يمكنه تنفيذ كود ضار.",
    fix:"استخدم Docker container sandbox أو RestrictedPython.",
    color: C.red,
  },
];

const MISSING = [
  { id:"M1", pri:"حرج", title:"Agent Registration عند Startup",
    body:"الـ lifespan() لا يسجل أي من الـ 24 agent في AgentRegistry. النظام يعمل بـ simulations فقط.",
    color:C.red },
  { id:"M2", pri:"حرج", title:"Alembic Database Migrations",
    body:"ensure_tables() تنفذ CREATE TABLE بدون versioning. خطرة في production — ممكن تفقد data.",
    color:C.red },
  { id:"M3", pri:"حرج", title:"Real Embeddings (FastEmbed / sentence-transformers)",
    body:"Skill Memory بلا vector search حقيقي. يجب استبدال SHA256 بـ embedding model.",
    color:C.red },
  { id:"M4", pri:"عالي", title:"Session Persistence في Redis",
    body:"self._sessions dict يُفقد عند كل restart. يجب حفظها في Redis.",
    color:C.amber },
  { id:"M5", pri:"عالي", title:"Input Validation & Sanitization",
    body:"لا validation على message field. prompt injection و XSS ممكنان.",
    color:C.amber },
  { id:"M6", pri:"عالي", title:"Real Web Search Integration",
    body:"web_search.py placeholder فقط. يجب ربطه بـ DuckDuckGo أو Serper.",
    color:C.amber },
  { id:"M7", pri:"عالي", title:"Browser Tool (Playwright)",
    body:"browser.py موجود كـ file لكن بلا implementation. مهم لـ research agents.",
    color:C.amber },
  { id:"M8", pri:"متوسط", title:"User-based Rate Limiting",
    body:"slowapi يحد بالـ IP فقط. لا per-user limits.",
    color:C.blue },
  { id:"M9", pri:"متوسط", title:"Prometheus Metrics Integration",
    body:"prometheus_client منصّب بس لا counters/histograms مستخدمة فعلياً.",
    color:C.blue },
];

const GOOD = [
  { text:"BaseAgent ABC Interface — 24 framework بـ interface موحد ✓", score:"10/10" },
  { text:"OpenAI-Compatible /v1/chat/completions — جديد وممتاز ✓", score:"10/10" },
  { text:"Frontend SSE Streaming حقيقي مع code block renderer ✓", score:"9/10" },
  { text:"RTL Arabic UI مع Noto Kufi + Playfair Display ✓", score:"9/10" },
  { text:"25 Agent Selector في الـ Frontend ✓", score:"9/10" },
  { text:"TaskGraph Topological Sort + Parallel Groups ✓", score:"9/10" },
  { text:"Intent Classifier 3-tier: Ollama → WindsurfAPI → Keyword ✓", score:"8/10" },
  { text:"LLM Router 4-tier مع complexity routing ✓", score:"8/10" },
  { text:"Memory Architecture: Redis + PostgreSQL + Qdrant ✓", score:"8/10" },
  { text:"Agent Simulation Fallback — يشتغل بدون frameworks ✓", score:"8/10" },
  { text:"Test Coverage: 21 test file ✓", score:"8/10" },
  { text:"Docker Compose 7 services مع healthchecks ✓", score:"8/10" },
  { text:"Helm Charts لـ Kubernetes ✓", score:"7/10" },
  { text:"stats fetch من /v1/agents و /metrics حقيقي ✓", score:"8/10" },
];

const ROADMAP = [
  {
    phase:"1", weeks:"أسبوع 1", title:"إصلاح الـ Blockers", color:C.red,
    tasks:[
      "إصلاح requirements.txt — 10 package names خاطئة",
      "إصلاح CORS — origins محددة بدل *",
      "إزالة os.environ mutation — مرر config مباشرةً",
      "إصلاح Auth — User model + database + get_user_manager",
      "استبدال SHA256 بـ FastEmbed في skill_memory",
    ],
  },
  {
    phase:"2", weeks:"أسبوع 2", title:"تفعيل الـ System", color:C.amber,
    tasks:[
      "Agent Registration في lifespan — تسجيل الـ 24 agent",
      "Alembic migrations — بدل ensure_tables()",
      "Session persistence في Redis — بدل in-memory dict",
      "Input validation — Pydantic validators + max_length",
      "إرسال activeAgent من Frontend للـ Backend",
    ],
  },
  {
    phase:"3", weeks:"أسبوع 3–4", title:"تكتمل الـ Tools", color:C.blue,
    tasks:[
      "Real Web Search — DuckDuckGo API integration",
      "Browser Tool — Playwright headless implementation",
      "Code Executor Sandbox — Docker container بدل exec()",
      "API Status indicator حقيقي في Frontend",
      "فلترة status chunks من /v1/chat/completions",
    ],
  },
  {
    phase:"4", weeks:"أسبوع 5–6", title:"Production Hardening", color:C.green,
    tasks:[
      "User-based Rate Limiting — per user_id",
      "Prometheus counters فعلية في الكود",
      "GPU-optional Docker profile",
      "Secret Management (نقل من .env لـ Vault)",
      "E2E Tests للـ /v1/chat/completions endpoint",
    ],
  },
];

// ─── COMPONENTS ────────────────────────────────────────────────

const mono = "'DM Mono', monospace";
const serif = "'Playfair Display', serif";

function Tag({ color, children, sm }) {
  return (
    <span style={{
      display:"inline-flex", alignItems:"center",
      background:color+"1e", border:`1px solid ${color}40`,
      color, borderRadius:5, padding: sm ? "1px 7px" : "3px 10px",
      fontSize: sm ? 9 : 11, fontWeight:700, letterSpacing:.5,
      whiteSpace:"nowrap", fontFamily:mono,
    }}>{children}</span>
  );
}

function ScoreBar({ label, score, color, max=10 }) {
  const pct = (score/max)*100;
  return (
    <div style={{marginBottom:10}}>
      <div style={{display:"flex", justifyContent:"space-between", marginBottom:4}}>
        <span style={{fontSize:11,color:C.textMuted,fontFamily:mono}}>{label}</span>
        <span style={{fontSize:12,fontWeight:700,color,fontFamily:mono}}>{score}/{max}</span>
      </div>
      <div style={{height:4,borderRadius:2,background:C.border}}>
        <div style={{height:4,borderRadius:2,background:color,width:`${pct}%`,transition:"width 0.6s"}}/>
      </div>
    </div>
  );
}

function CriticalCard({ bug }) {
  const [open, setOpen] = useState(false);
  const fixed = bug.status === "مُصلحت";
  return (
    <div onClick={()=>setOpen(!open)} style={{
      background: fixed ? C.greenBg : C.redBg,
      border:`1px solid ${fixed ? C.green : C.red}30`,
      borderRadius:10, overflow:"hidden", cursor:"pointer",
      boxShadow:open ? `0 0 24px ${fixed?C.green:C.red}12` : "none",
      transition:"box-shadow 0.2s",
    }}>
      <div style={{
        display:"flex", alignItems:"center", gap:12,
        padding:"14px 18px",
        background:open ? (fixed?C.green:C.red)+"0c" : "transparent",
      }}>
        <div style={{
          width:30, height:30, borderRadius:7,
          background:(fixed?C.green:C.red)+"25",
          border:`1px solid ${fixed?C.green:C.red}50`,
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:10, fontWeight:800, color:fixed?C.green:C.red, fontFamily:mono, flexShrink:0,
        }}>{bug.id}</div>
        <div style={{flex:1}}>
          <div style={{display:"flex", alignItems:"center", gap:8, marginBottom:3}}>
            <Tag color={fixed?C.green:C.red}>{fixed?"✓ مُصلح":"✗ لم تُصلح"}</Tag>
            <span style={{fontSize:10,color:C.textDim,fontFamily:mono}}>{bug.file}</span>
          </div>
          <div style={{fontSize:13,fontWeight:600,color:fixed?C.greenSoft:C.redSoft}}>{bug.title}</div>
        </div>
        <span style={{color:C.textDim,fontSize:11,transform:open?"rotate(180deg)":"none",transition:"0.2s",flexShrink:0}}>▼</span>
      </div>
      {open && (
        <div style={{padding:"0 18px 16px", borderTop:`1px solid ${fixed?C.green:C.red}20`}}>
          <div style={{marginTop:14, display:"grid", gridTemplateColumns:"1fr 1fr", gap:14}}>
            <div>
              <div style={{fontSize:9,color:C.red,letterSpacing:2,marginBottom:7,fontFamily:mono}}>المشكلة</div>
              <pre style={{
                background:"#0a0303", border:`1px solid ${C.red}18`,
                borderRadius:7, padding:"10px 12px",
                fontSize:11, color:"#fca5a5", fontFamily:mono,
                whiteSpace:"pre-wrap", lineHeight:1.7, margin:0,
              }}>{bug.detail}</pre>
            </div>
            <div>
              <div style={{fontSize:9,color:C.green,letterSpacing:2,marginBottom:7,fontFamily:mono}}>الحل</div>
              <pre style={{
                background:"#030a03", border:`1px solid ${C.green}18`,
                borderRadius:7, padding:"10px 12px",
                fontSize:11, color:"#86efac", fontFamily:mono,
                whiteSpace:"pre-wrap", lineHeight:1.7, margin:0,
              }}>{bug.fix}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BugRow({ bug }) {
  const [open, setOpen] = useState(false);
  return (
    <div onClick={()=>setOpen(!open)} style={{
      background:C.surface, border:`1px solid ${bug.color}20`,
      borderRadius:9, padding:"11px 15px", cursor:"pointer",
      transition:"border-color 0.2s",
    }}>
      <div style={{display:"flex", alignItems:"flex-start", gap:10}}>
        <div style={{
          width:26, height:26, borderRadius:6,
          background:bug.color+"20", border:`1px solid ${bug.color}40`,
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:9, fontWeight:800, color:bug.color, fontFamily:mono, flexShrink:0, marginTop:1,
        }}>{bug.id}</div>
        <div style={{flex:1}}>
          <div style={{display:"flex", gap:7, alignItems:"center", marginBottom:4}}>
            <Tag color={bug.color} sm>{bug.sev}</Tag>
            <span style={{fontSize:9,color:C.textDim,fontFamily:mono}}>{bug.file}</span>
          </div>
          <div style={{fontSize:12,fontWeight:600,color:C.text,marginBottom:3}}>{bug.title}</div>
          <div style={{fontSize:11,color:C.textMuted,lineHeight:1.6}}>{bug.body}</div>
          {open && (
            <div style={{
              marginTop:9, background:"#030a03",
              border:`1px solid ${C.green}18`, borderRadius:7, padding:"9px 12px",
            }}>
              <div style={{fontSize:9,color:C.green,letterSpacing:2,marginBottom:5,fontFamily:mono}}>FIX →</div>
              <pre style={{fontSize:11,color:"#86efac",fontFamily:mono,whiteSpace:"pre-wrap",lineHeight:1.7,margin:0}}>{bug.fix}</pre>
            </div>
          )}
        </div>
        <span style={{fontSize:10,color:C.textDim,transform:open?"rotate(180deg)":"none",transition:"0.2s",flexShrink:0}}>▼</span>
      </div>
    </div>
  );
}

function MissingRow({ item }) {
  return (
    <div style={{
      background:C.surface, border:`1px solid ${item.color}18`,
      borderRadius:8, padding:"10px 14px",
      display:"flex", gap:10, alignItems:"flex-start",
    }}>
      <Tag color={item.color}>{item.id}</Tag>
      <div>
        <div style={{display:"flex", gap:7, alignItems:"center", marginBottom:4}}>
          <span style={{fontSize:12,fontWeight:600,color:C.text,fontFamily:mono}}>{item.title}</span>
          <Tag color={item.color} sm>{item.pri}</Tag>
        </div>
        <div style={{fontSize:11,color:C.textMuted,lineHeight:1.6}}>{item.body}</div>
      </div>
    </div>
  );
}

function NewFeatureCard({ item }) {
  return (
    <div style={{
      background:C.greenBg, border:`1px solid ${item.color}30`,
      borderRadius:10, padding:"14px 16px",
    }}>
      <div style={{display:"flex", alignItems:"flex-start", gap:12}}>
        <div style={{
          width:32, height:32, borderRadius:8,
          background:item.color+"20", border:`1px solid ${item.color}40`,
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:16, color:item.color, flexShrink:0,
        }}>{item.icon}</div>
        <div style={{flex:1}}>
          <div style={{display:"flex", gap:7, alignItems:"center", marginBottom:6}}>
            <span style={{fontSize:13,fontWeight:700,color:item.color}}>{item.title}</span>
            <Tag color={item.color} sm>{item.quality}</Tag>
          </div>
          <div style={{fontSize:10,color:C.textDim,fontFamily:mono,marginBottom:5}}>{item.file}</div>
          <div style={{fontSize:12,color:C.textMuted,lineHeight:1.65}}>{item.detail}</div>
        </div>
      </div>
    </div>
  );
}

function RoadmapCard({ p }) {
  return (
    <div style={{
      background:p.color+"08", border:`1px solid ${p.color}28`,
      borderRadius:10, padding:"15px 17px",
    }}>
      <div style={{display:"flex", alignItems:"center", gap:10, marginBottom:12}}>
        <div style={{
          width:30, height:30, borderRadius:7,
          background:p.color+"22", border:`1px solid ${p.color}45`,
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:11, fontWeight:800, color:p.color, fontFamily:mono, flexShrink:0,
        }}>P{p.phase}</div>
        <div>
          <div style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:mono}}>{p.title}</div>
          <Tag color={p.color} sm>{p.weeks}</Tag>
        </div>
      </div>
      {p.tasks.map((t,i)=>(
        <div key={i} style={{display:"flex", gap:9, marginBottom:7, alignItems:"flex-start"}}>
          <div style={{
            width:18, height:18, borderRadius:4,
            background:p.color+"15", border:`1px solid ${p.color}25`,
            display:"flex", alignItems:"center", justifyContent:"center",
            fontSize:8, color:p.color, fontWeight:700, fontFamily:mono, flexShrink:0, marginTop:1,
          }}>{i+1}</div>
          <span style={{fontSize:11,color:C.textMuted,lineHeight:1.6,fontFamily:mono}}>{t}</span>
        </div>
      ))}
    </div>
  );
}

// ─── MAIN ────────────────────────────────────────────────────────

export default function AuditV6() {
  const [tab, setTab] = useState("overview");

  const TABS = [
    {id:"overview", label:"نظرة عامة",      color:C.purple},
    {id:"new",      label:"✓ الجديد v6",    color:C.green,  count:3},
    {id:"critical", label:"Critical Bugs",  color:C.red,    count:5},
    {id:"bugs",     label:"Bugs",           color:C.amber,  count:8},
    {id:"missing",  label:"ناقص",           color:C.blue,   count:9},
    {id:"good",     label:"نقاط القوة",     color:C.teal,   count:14},
    {id:"roadmap",  label:"خطة الإصلاح",   color:C.purpleSoft},
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Mono:wght@400;500&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        ::-webkit-scrollbar{width:4px;}
        ::-webkit-scrollbar-thumb{background:#2A2A45;border-radius:2px;}
      `}</style>

      <div style={{minHeight:"100vh",background:C.bg,fontFamily:mono,color:C.text}}>

        {/* HERO */}
        <div style={{
          background:`radial-gradient(ellipse 80% 50% at 50% -10%, ${C.purpleDeep}22 0%, transparent 70%)`,
          borderBottom:`1px solid ${C.border}`,
          padding:"44px 48px 36px", position:"relative", overflow:"hidden",
        }}>
          <div style={{
            position:"absolute", inset:0,
            backgroundImage:`radial-gradient(circle, ${C.purple}10 1px, transparent 1px)`,
            backgroundSize:"28px 28px", pointerEvents:"none",
          }}/>
          <div style={{position:"relative"}}>
            <div style={{display:"inline-flex", alignItems:"center", gap:8,
              background:C.green+"15", border:`1px solid ${C.green}35`,
              borderRadius:8, padding:"5px 14px", marginBottom:18}}>
              <div style={{width:7,height:7,borderRadius:"50%",background:C.green,boxShadow:`0 0 8px ${C.green}`}}/>
              <span style={{fontSize:11,color:C.greenSoft,letterSpacing:2}}>JNUS.1 — FULL PROJECT AUDIT v6</span>
            </div>

            <h1 style={{fontFamily:serif, fontSize:34, fontWeight:700, color:C.lavender, lineHeight:1.2, marginBottom:12}}>
              تقرير المراجعة الشاملة<br/>
              <span style={{background:`linear-gradient(135deg,${C.purple},${C.purpleSoft})`,
                WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent"}}>
                Jnus.1 — Version 6
              </span>
            </h1>

            <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,maxWidth:580,marginBottom:26}}>
              مقارنة كاملة بين v5 و v6. ما الذي تغيّر، ما الذي أُصلح، ما البقي كما هو، وما الخطوات القادمة.
            </p>

            {/* Stats grid */}
            <div style={{display:"flex", gap:16, flexWrap:"wrap"}}>
              {[
                {n:"3",  label:"جديد في v6",    color:C.green},
                {n:"0",  label:"Bugs مُصلحة",   color:C.red},
                {n:"5",  label:"Critical Bugs", color:C.red},
                {n:"8",  label:"Regular Bugs",  color:C.amber},
                {n:"9",  label:"ناقص",          color:C.blue},
                {n:"24", label:"Agents",        color:C.purple},
                {n:"107",label:"ملفات",         color:C.teal},
              ].map((s,i)=>(
                <div key={i} style={{
                  background:s.color+"10", border:`1px solid ${s.color}28`,
                  borderRadius:8, padding:"10px 16px", textAlign:"center",
                }}>
                  <div style={{fontFamily:serif, fontSize:24, fontWeight:700, color:s.color}}>{s.n}</div>
                  <div style={{fontSize:10, color:C.textDim, marginTop:3}}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* TABS */}
        <div style={{
          display:"flex", gap:4, padding:"12px 48px",
          borderBottom:`1px solid ${C.border}`, background:C.surface,
          overflowX:"auto",
        }}>
          {TABS.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} style={{
              background:tab===t.id ? t.color+"22" : "transparent",
              border:`1px solid ${tab===t.id ? t.color+"55" : "transparent"}`,
              borderRadius:8, padding:"7px 16px", cursor:"pointer",
              display:"flex", alignItems:"center", gap:7,
              fontFamily:mono, fontSize:11,
              color:tab===t.id ? t.color : C.textDim,
              whiteSpace:"nowrap", transition:"all 0.15s",
            }}>
              {t.label}
              {t.count && (
                <span style={{
                  background:t.color+"30", border:`1px solid ${t.color}40`,
                  borderRadius:4, padding:"1px 6px", fontSize:9, color:t.color,
                }}>{t.count}</span>
              )}
            </button>
          ))}
        </div>

        {/* CONTENT */}
        <div style={{padding:"32px 48px", maxWidth:1100, margin:"0 auto"}}>

          {/* OVERVIEW */}
          {tab==="overview" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.lavender,marginBottom:20}}>
                ملخص المشروع
              </h2>
              <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20, marginBottom:24}}>
                {/* Structure */}
                <div style={{background:C.surface,border:`1px solid ${C.border}`,borderRadius:10,padding:20}}>
                  <div style={{fontSize:10,color:C.textDim,letterSpacing:2,marginBottom:14}}>هيكل المشروع</div>
                  {[
                    {label:"ملفات Python",     val:47,   color:C.purple},
                    {label:"Agent Files",      val:24,   color:C.blue},
                    {label:"Test Files",       val:21,   color:C.green},
                    {label:"Frontend Files",   val:6,    color:C.teal},
                    {label:"Docker/K8s Files", val:9,    color:C.amber},
                    {label:"Docs/Markdown",    val:5,    color:C.orange},
                  ].map((r,i)=>(
                    <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
                      <span style={{fontSize:11,color:C.textMuted}}>{r.label}</span>
                      <span style={{fontSize:12,fontWeight:700,color:r.color,fontFamily:mono}}>{r.val}</span>
                    </div>
                  ))}
                </div>

                {/* Scores */}
                <div style={{background:C.surface,border:`1px solid ${C.border}`,borderRadius:10,padding:20}}>
                  <div style={{fontSize:10,color:C.textDim,letterSpacing:2,marginBottom:14}}>تقييم الجودة</div>
                  <ScoreBar label="Architecture Design"    score={9} color={C.green}  />
                  <ScoreBar label="Frontend Quality (v6)"  score={8} color={C.green}  />
                  <ScoreBar label="Code Quality"           score={7} color={C.blue}   />
                  <ScoreBar label="API Design"             score={7} color={C.blue}   />
                  <ScoreBar label="Test Coverage"          score={6} color={C.amber}  />
                  <ScoreBar label="Production Readiness"   score={3} color={C.red}    />
                </div>
              </div>

              {/* v5 vs v6 comparison */}
              <div style={{background:C.surface,border:`1px solid ${C.border}`,borderRadius:10,padding:20,marginBottom:20}}>
                <div style={{fontSize:10,color:C.textDim,letterSpacing:2,marginBottom:16}}>مقارنة v5 → v6</div>
                <div style={{display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:3}}>
                  {[
                    {item:"requirements.txt",         v5:"❌ مكسور",   v6:"❌ مكسور",   same:true},
                    {item:"Auth System",              v5:"❌ مكسور",   v6:"❌ مكسور",   same:true},
                    {item:"CORS Config",              v5:"❌ خاطئ",    v6:"❌ خاطئ",    same:true},
                    {item:"os.environ mutation",      v5:"❌ موجودة",  v6:"❌ موجودة",  same:true},
                    {item:"Skill Memory Embedding",   v5:"❌ SHA256",  v6:"❌ SHA256",  same:true},
                    {item:"Agent Registration",       v5:"❌ ناقص",    v6:"❌ ناقص",    same:true},
                    {item:"Frontend UI",              v5:"⚠ أساسية", v6:"✓ كاملة",   same:false},
                    {item:"SSE Streaming Client",     v5:"❌ ناقص",    v6:"✓ مكتمل",  same:false},
                    {item:"OpenAI-Compatible API",    v5:"❌ ناقص",    v6:"✓ مضاف",   same:false},
                    {item:"25 Agent Selector",        v5:"❌ ناقص",    v6:"✓ مضاف",   same:false},
                    {item:"Web Search Tool",          v5:"⚠ Fake",   v6:"⚠ Fake",   same:true},
                    {item:"Code Executor Sandbox",    v5:"❌ unsafe", v6:"❌ unsafe",  same:true},
                  ].map((r,i)=>(
                    <div key={i} style={{
                      background:r.same ? C.redBg : C.greenBg,
                      border:`1px solid ${r.same ? C.red : C.green}15`,
                      borderRadius:6, padding:"8px 11px",
                    }}>
                      <div style={{fontSize:10,color:C.textDim,marginBottom:3,fontFamily:mono}}>{r.item}</div>
                      <div style={{display:"flex",justifyContent:"space-between",gap:4}}>
                        <span style={{fontSize:10,color:C.red,fontFamily:mono}}>v5: {r.v5}</span>
                        <span style={{fontSize:10,color:r.same?C.red:C.green,fontFamily:mono}}>v6: {r.v6}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Key insight */}
              <div style={{
                background:`linear-gradient(135deg,${C.purple}10,${C.blue}08)`,
                border:`1px solid ${C.purple}28`, borderRadius:10, padding:20,
              }}>
                <div style={{fontSize:10,color:C.purple,letterSpacing:2,marginBottom:12}}>الخلاصة الحقيقية</div>
                <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12}}>
                  {[
                    {label:"ما تغيّر في v6",       val:"Frontend كامل + OpenAI API endpoint + chat route", color:C.green},
                    {label:"ما لم يتغيّر",         val:"كل الـ Python core bugs موجودة كما هي تماماً",       color:C.red},
                    {label:"الأولوية القادمة",      val:"إصلاح requirements.txt + Auth + CORS أولاً",       color:C.amber},
                    {label:"وقت للـ Production",    val:"6 أسابيع إصلاح + testing + deployment",            color:C.blue},
                  ].map((v,i)=>(
                    <div key={i} style={{background:C.surface,border:`1px solid ${v.color}20`,borderRadius:8,padding:12}}>
                      <div style={{fontSize:10,color:C.textDim,marginBottom:5}}>{v.label}</div>
                      <div style={{fontSize:12,color:v.color,fontFamily:mono,lineHeight:1.5}}>{v.val}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* NEW IN V6 */}
          {tab==="new" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.green,marginBottom:8}}>
                الجديد في v6 — 3 تحسينات حقيقية
              </h2>
              <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,marginBottom:20}}>
                هذه التحسينات حقيقية ومهمة. Frontend أصبح يعمل مع الـ backend فعلاً.
              </p>
              <div style={{display:"flex",flexDirection:"column",gap:12}}>
                {WHATS_NEW.map((n,i)=><NewFeatureCard key={i} item={n}/>)}
              </div>
            </div>
          )}

          {/* CRITICAL */}
          {tab==="critical" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.red,marginBottom:8}}>
                الـ 5 Critical Bugs — لم تُصلح أي منها
              </h2>
              <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,marginBottom:20}}>
                هذه الـ bugs ستمنع المشروع من الـ startup. اضغط على أي card للتفاصيل والحل.
              </p>
              <div style={{display:"flex",flexDirection:"column",gap:10}}>
                {CRITICAL_BUGS.map(b=><CriticalCard key={b.id} bug={b}/>)}
              </div>
            </div>
          )}

          {/* BUGS */}
          {tab==="bugs" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.amber,marginBottom:8}}>
                الـ 8 Bugs — 4 جديدة في v6
              </h2>
              <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,marginBottom:20}}>
                اضغط على أي card لتشوف الحل المقترح.
              </p>
              <div style={{display:"flex",flexDirection:"column",gap:8}}>
                {BUGS_V6.map(b=><BugRow key={b.id} bug={b}/>)}
              </div>
            </div>
          )}

          {/* MISSING */}
          {tab==="missing" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.blue,marginBottom:8}}>
                الـ 9 نواقص — ضرورية للـ Production
              </h2>
              <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,marginBottom:20}}>
                Features مذكورة في الـ architecture لكن مش موجودة أو placeholder فقط.
              </p>
              <div style={{display:"flex",flexDirection:"column",gap:8}}>
                {MISSING.map(m=><MissingRow key={m.id} item={m}/>)}
              </div>
            </div>
          )}

          {/* GOOD */}
          {tab==="good" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.teal,marginBottom:8}}>
                نقاط القوة — 14 جانب ممتاز
              </h2>
              <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,marginBottom:20}}>
                المشروع عنده architecture قوية جداً. المشاكل في التنفيذ مش في التصميم.
              </p>
              <div style={{display:"flex",flexDirection:"column",gap:7}}>
                {GOOD.map((g,i)=>(
                  <div key={i} style={{
                    background:C.greenBg, border:`1px solid ${C.green}20`,
                    borderRadius:8, padding:"11px 15px",
                    display:"flex", alignItems:"center", justifyContent:"space-between", gap:12,
                  }}>
                    <div style={{display:"flex",alignItems:"center",gap:10}}>
                      <div style={{
                        width:22, height:22, borderRadius:5,
                        background:C.green+"22", border:`1px solid ${C.green}40`,
                        display:"flex", alignItems:"center", justifyContent:"center",
                        fontSize:11, color:C.green, flexShrink:0,
                      }}>✓</div>
                      <span style={{fontSize:12,color:C.greenSoft,lineHeight:1.6}}>{g.text}</span>
                    </div>
                    <Tag color={C.green} sm>{g.score}</Tag>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ROADMAP */}
          {tab==="roadmap" && (
            <div>
              <h2 style={{fontFamily:serif,fontSize:22,fontWeight:700,color:C.purple,marginBottom:8}}>
                خطة الإصلاح — 6 أسابيع للـ Production
              </h2>
              <p style={{fontSize:13,color:C.textMuted,lineHeight:1.7,marginBottom:20}}>
                لا تبدأ الـ Phase 2 قبل إكمال الـ Phase 1. كل phase قابلة للـ demo بشكل مستقل.
              </p>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:20}}>
                {ROADMAP.map(p=><RoadmapCard key={p.phase} p={p}/>)}
              </div>

              {/* Final verdict */}
              <div style={{
                background:`linear-gradient(135deg,${C.purple}10,${C.blue}08)`,
                border:`1px solid ${C.purple}28`, borderRadius:12, padding:22,
              }}>
                <div style={{fontSize:10,color:C.purple,letterSpacing:2,marginBottom:14}}>
                  FINAL VERDICT — الحكم النهائي على v6
                </div>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:12}}>
                  {[
                    {label:"Architecture",     score:"9.5/10", color:C.green,  note:"هيكل عالمي حقيقي"},
                    {label:"Frontend v6",      score:"8/10",   color:C.green,  note:"تحسن كبير — SSE يعمل"},
                    {label:"Backend Core",     score:"6/10",   color:C.amber,  note:"جيد لكن bugs موجودة"},
                    {label:"Production Ready", score:"2/10",   color:C.red,    note:"يحتاج 6 أسابيع إصلاح"},
                  ].map((v,i)=>(
                    <div key={i} style={{
                      background:C.surface, border:`1px solid ${v.color}25`,
                      borderRadius:8, padding:"12px 14px", textAlign:"center",
                    }}>
                      <div style={{fontFamily:serif,fontSize:22,fontWeight:700,color:v.color,marginBottom:4}}>{v.score}</div>
                      <div style={{fontSize:10,color:C.textMuted,marginBottom:6}}>{v.label}</div>
                      <div style={{fontSize:10,color:C.textDim,lineHeight:1.4}}>{v.note}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* FOOTER */}
        <div style={{
          borderTop:`1px solid ${C.border}`, padding:"16px 48px",
          background:C.surface, display:"flex", justifyContent:"space-between",
          alignItems:"center", flexWrap:"wrap", gap:12,
        }}>
          <span style={{fontSize:11,color:C.textDim}}>
            Jnus.1 v6 Audit — 3 جديد · 5 Critical · 8 Bugs · 9 Missing · 14 نقاط قوة
          </span>
          <div style={{display:"flex",gap:7}}>
            {[["v6 Frontend ✓",C.green],["Core Bugs باقية",C.red],["6 أسابيع للإصلاح",C.amber]].map(([t,c],i)=>(
              <Tag key={i} color={c} sm>{t}</Tag>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
