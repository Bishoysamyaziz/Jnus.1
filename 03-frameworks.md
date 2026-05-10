# Phase 3 — Framework Integration (Week 5–8)
> دمج الـ 24 Framework في نظام واحد. الأصعب والأهم.

---

## المبدأ الأساسي

```python
# packages/agents/base.py

class BaseAgent(ABC):
    """
    Interface موحد لكل الـ 24 framework.
    كل framework بيشتغل في isolation.
    الـ Orchestrator بيتكلم مع BaseAgent فقط — مش مع الـ framework مباشرة.
    """
    
    @abstractmethod
    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        pass
    
    @abstractmethod
    def get_capabilities(self) -> list[Capability]:
        """إيه اللي الـ agent ده شاطر فيه؟"""
        pass
    
    @abstractmethod
    def estimate_cost(self, task: Task) -> CostEstimate:
        """هيكلف قد إيه؟"""
        pass
    
    @property
    @abstractmethod
    def framework_name(self) -> str:
        pass
```

---

## الـ 24 Framework — التفاصيل

### Group A: Multi-Agent Orchestrators (Week 5)

#### 1. CrewAI Agent
```python
# packages/agents/crewai_agent.py
class CrewAIAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج أدوار متعددة (researcher + writer + reviewer)
    مثال: "اكتب تقرير بحثي شامل عن X"
    
    الـ Crew:
    - Researcher: يجمع المعلومات
    - Analyst: يحللها
    - Writer: يكتب التقرير
    - Reviewer: يراجع ويصحح
    """
    
    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        crew = Crew(
            agents=[self.researcher, self.analyst, self.writer, self.reviewer],
            tasks=self._build_tasks(task),
            process=Process.sequential,
            memory=True,
            verbose=False
        )
        result = await crew.kickoff_async(inputs={"task": task.description})
        return AgentResult(content=result, framework="crewai")
```

#### 2. AutoGen Agent
```python
# packages/agents/autogen_agent.py
class AutoGenAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج نقاش بين agents (debate, critique, verification)
    مثال: "راجع هذا الكود وتأكد إنه secure"
    
    Group:
    - Coder: يكتب/يقرأ الكود
    - Critic: ينتقد ويقترح
    - Security Expert: يفحص الأمان
    - Verifier: يتأكد من النتيجة
    """
```

#### 3. MetaGPT Agent
```python
# packages/agents/metagpt_agent.py
class MetaGPTAgent(BaseAgent):
    """
    متى يُستدعى: مهام software engineering كاملة
    مثال: "ابني SaaS app للـ task management"
    
    13 دور:
    ProductManager, Architect, ProjectManager, Engineer(×3),
    QA Engineer, DevOps, Designer, DataAnalyst, 
    Researcher, Writer, Reviewer
    """
```

#### 4. CAMEL Agent
```python
# packages/agents/camel_agent.py
class CAMELAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج تخصص عميق في مجال واحد
    مثال: "حلل هذا الـ dataset وأعطيني insights"
    
    12 agent متخصص:
    ChatAgent, CriticAgent, KnowledgeGraphAgent,
    TaskCreationAgent, TaskPrioritizationAgent, ...
    """
```

### Group B: Planning & Execution (Week 6)

#### 5. AgentVerse Agent
```python
# packages/agents/agentverse_agent.py
class AgentVerseAgent(BaseAgent):
    """
    متى يُستدعى: simulation scenarios + complex tasksolving
    مثال: "محاكاة team اشتغل على مشكلة X"
    
    يستخدم config.yaml من agentverse/tasks/
    """
```

#### 6. TaskWeaver Agent
```python
# packages/agents/taskweaver_agent.py
class TaskWeaverAgent(BaseAgent):
    """
    متى يُستدعى: تحليل بيانات + Python execution
    مثال: "حلل هذا الـ CSV وارسم الـ trends"
    
    يولد Python code ينفذه في sandbox
    """
```

#### 7. BabyAGI Agent
```python
# packages/agents/babyagi_agent.py
class BabyAGIAgent(BaseAgent):
    """
    متى يُستدعى: أهداف طويلة المدى تحتاج prioritization مستمر
    مثال: "خطط لـ 3 أشهر لتعلم machine learning"
    
    Loop: Create Tasks → Prioritize → Execute → Create More
    """
```

#### 8. Swarm Agent
```python
# packages/agents/swarm_agent.py
class SwarmAgent(BaseAgent):
    """
    متى يُستدعى: routing بين specialists بناءً على context
    مثال: تبدأ مع general agent وتتحول لـ specialist
    
    يستخدم OpenAI Swarm handoff mechanism
    """
```

### Group C: Code & Dev Agents (Week 7)

#### 9. Aider Agent
```python
# packages/agents/aider_agent.py
class AiderAgent(BaseAgent):
    """
    متى يُستدعى: تعديل كود موجود (refactor, bugfix, feature add)
    مثال: "أضف unit tests لهذا الـ module"
    
    يعمل على git repository حقيقي
    """
```

#### 10. OpenHands Agent
```python
# packages/agents/openhands_agent.py
class OpenHandsAgent(BaseAgent):
    """
    متى يُستدعى: مهام dev environment كاملة (install, run, debug)
    مثال: "خذ هذا المشروع وأصلح الـ failing tests"
    
    بيتحكم في terminal حقيقي
    """
```

#### 11. smolagents Agent
```python
# packages/agents/smolagents_agent.py
class SmolAgentsAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج tool calling سريع
    يدعم: CodeAgent, ToolCallingAgent, MultiStepAgent
    """
```

#### 12. HuggingFace Agent
```python
# packages/agents/huggingface_agent.py
class HuggingFaceAgent(BaseAgent):
    """
    متى يُستدعى: ML tasks, model inference, transformers
    مثال: "صنف الصور دي", "ترجم هذا النص"
    """
```

### Group D: RAG & Knowledge (Week 7)

#### 13. LangChain Agent
```python
# packages/agents/langchain_agent.py
class LangChainAgent(BaseAgent):
    """
    متى يُستدعى: chain of thought + tool use عام
    الأكثر flexibility — fallback للحالات غير المصنفة
    """
```

#### 14. LangGraph Agent
```python
# packages/agents/langgraph_agent.py
class LangGraphAgent(BaseAgent):
    """
    متى يُستدعى: workflows معقدة مع state management
    مثال: approval flows, conditional branching
    """
```

#### 15. Haystack Agent
```python
# packages/agents/haystack_agent.py
class HaystackAgent(BaseAgent):
    """
    متى يُستدعى: RAG على documents + knowledge retrieval
    مثال: "ابحث في هذه الوثائق وأجب على السؤال"
    """
```

#### 16. LlamaIndex Agent
```python
# packages/agents/llamaindex_agent.py
class LlamaIndexAgent(BaseAgent):
    """
    متى يُستدعى: document QA + structured data query
    مثال: "اسأل على هذا الـ PDF"
    """
```

#### 17. Semantic Kernel Agent
```python
# packages/agents/semantic_kernel_agent.py
class SemanticKernelAgent(BaseAgent):
    """
    متى يُستدعى: Azure AI, Bedrock, CopilotStudio integration
    مثال: enterprise workflows مع Microsoft stack
    """
```

### Group E: Memory & Conversation (Week 8)

#### 18. Letta Agent
```python
# packages/agents/letta_agent.py
class LettaAgent(BaseAgent):
    """
    متى يُستدعى: conversations تحتاج long-term memory عبر sessions
    مثال: personal assistant يتذكر كل تفاصيلك
    
    يستخدم MemGPT memory management
    """
```

#### 19. Mem0 Agent
```python
# packages/agents/mem0_agent.py
class Mem0Agent(BaseAgent):
    """
    متى يُستدعى: cross-session personality + preferences
    يُضاف لكل agent آخر كـ memory layer
    """
```

#### 20. AutoGPT Agent
```python
# packages/agents/autogpt_agent.py
class AutoGPTAgent(BaseAgent):
    """
    متى يُستدعى: self-directed tasks تحتاج autonomy عالية
    مثال: "ابحث عن أفضل framework لـ X وقيّمه وأعطيني تقرير"
    """
```

#### 21. AgentGPT Agent
```python
# packages/agents/agentgpt_agent.py
class AgentGPTAgent(BaseAgent):
    """
    متى يُستدعى: goal decomposition + web-based research
    يستخدم agentgpt/packages/ الموجودة في المشروع
    """
```

### Group F: Conversational (Week 8)

#### 22. Rasa Agent
```python
# packages/agents/rasa_agent.py
class RasaAgent(BaseAgent):
    """
    متى يُستدعى: structured conversations + form filling
    مثال: "اجمع معلومات المستخدم خطوة بخطوة"
    """
```

#### 23. Botpress Agent
```python
# packages/agents/botpress_agent.py
class BotpressAgent(BaseAgent):
    """
    متى يُستدعى: visual flow conversations + NLU
    مثال: customer support بـ decision trees
    """
```

#### 24. SuperAGI Agent
```python
# packages/agents/superagi_agent.py
class SuperAGIAgent(BaseAgent):
    """
    متى يُستدعى: autonomous tasks مع 15 tool (GitHub, Jira, Slack...)
    مثال: "أنشئ Jira ticket وـassign للـ team وابعت Slack notification"
    
    Tools: GitHub, Jira, Slack, Email, Twitter, Google Calendar,
           Google Search, File, Code, Image Gen, Notion, Airtable,
           Zapier, HubSpot, Zendesk
    """
```

---

## Agent Selection Logic

```python
# packages/core/agent_selector.py

AGENT_ROUTING = {
    "CODE":         ["aider", "openhands", "smolagents", "metagpt"],
    "RESEARCH":     ["langchain", "haystack", "llamaindex", "crewai"],
    "CREATIVE":     ["crewai", "autogen", "langchain"],
    "DATA":         ["taskweaver", "camel", "langchain"],
    "AUTOMATION":   ["superagi", "autogpt", "agentgpt"],
    "CONVERSATION": ["letta", "mem0", "rasa"],
    "PLANNING":     ["babyagi", "metagpt", "crewai"],
    "EXECUTION":    ["swarm", "agentverse", "autogen"],
}

async def select_agent(intent: Intent, skill_memory: SkillMemory) -> list[str]:
    # 1. جرب من الذاكرة أولاً
    best = await skill_memory.get_best(intent.type)
    if best and best.confidence > 0.8:
        return [best.agent]
    
    # 2. fallback للـ routing table
    return AGENT_ROUTING.get(intent.type, ["langchain"])
```

---

## Acceptance Criteria

- [ ] كل framework يشتغل بشكل مستقل في isolation
- [ ] `BaseAgent.execute()` مكمّل لكل الـ 24 framework
- [ ] Agent selection يختار الـ framework الصح لكل intent
- [ ] Framework failure لا تأثر على باقي الـ frameworks
- [ ] كل agent يرجع `AgentResult` بنفس الـ structure
