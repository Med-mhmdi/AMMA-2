# AMMA LLM and Memory Comparison

This document supports Task Block 2: Multi-Agent System.  
It explains the LLM options considered for AMMA and the memory management options considered for the agentic workflow.

---

# 1. LLM Comparison

The AMMA Agent requires a model that can understand financial requests, extract structured JSON actions, support local deployment, and work inside an isolated environment. Since the project is deployed as a microservices system, local models through Ollama are preferred because they are easier to run in Docker-based environments and do not require sending private financial data to external APIs.

## 1.1 Compared LLM Options

| Model | Type | Strengths | Weaknesses | Suitability for AMMA |
|---|---|---|---|---|
| **Qwen2.5:7B** | Text LLM | Good instruction following, strong structured output, good JSON generation, works well with financial command extraction, runs locally through Ollama. | Requires enough RAM/VRAM, can still produce invalid JSON in some cases, not a vision model. | **Selected as main text model** because AMMA needs reliable command extraction, routing, clarification, and advice generation. |
| **Llama 3.1 / Llama 3.2** | Text LLM | Strong general reasoning, good conversational ability, good open-source ecosystem, widely used. | May require more resources depending on model size, JSON output may need strict prompting and post-processing. | Good alternative for advisor and conversation tasks, but Qwen was preferred for structured command extraction. |
| **Mistral 7B** | Text LLM | Fast, lightweight, good for local deployment, efficient for simple tasks. | May be weaker than Qwen for strict JSON extraction and complex multi-turn financial commands. | Useful fallback model for lightweight local execution, but less preferred for AMMA command extraction. |
| **Gemma 2 / Gemma 3** | Text LLM | Lightweight, can run locally, good for simple classification and summarization. | May be less consistent for strict tool-use JSON, depending on quantization and prompt design. | Possible for simple routing or summarization, but not selected as the main model. |
| **LLaVA** | Vision-language model | Can process receipt images and extract text or financial information from images. Runs locally through Ollama. | Vision extraction quality depends on image clarity; may hallucinate fields; not ideal for pure text command reasoning. | **Selected for vision tasks** such as receipt/image understanding. |
| **Cloud API models** | Text/Vision LLM | Usually strong reasoning and stable outputs, no local hardware limitations. | Requires internet access, may cost money, sends financial data outside the local environment, weaker privacy control. | Not selected for the main project because AMMA focuses on local/private deployment. |

---

## 1.2 Selected LLM Strategy

AMMA uses a **multi-model strategy**:

| Task | Selected Model Type | Reason |
|---|---|---|
| Intent routing | Qwen2.5:7B or similar text LLM | Understands user intent and routes to the correct agent. |
| Command extraction | Qwen2.5:7B | Good at converting natural language into structured JSON actions. |
| Clarification | Qwen2.5:7B | Generates natural missing-field questions. |
| Financial advice | Qwen2.5:7B or similar text LLM | Produces explanations and recommendations from financial context. |
| Notification decision | Qwen2.5:7B | Decides whether a warning or recommendation should become a notification. |
| Receipt/image extraction | LLaVA | Supports vision input and local image understanding. |

---

## 1.3 Final LLM Choice

The selected architecture uses:

- **Qwen2.5:7B** as the main text LLM.
- **LLaVA** as the vision model for image/receipt extraction.
- **Ollama** as the local LLM runtime.

This choice is suitable because it provides:

1. Local execution.
2. Better privacy for financial data.
3. Compatibility with Docker-based deployment.
4. Support for open-source models.
5. Good structured command extraction.
6. Vision support through a separate model.
7. No dependency on paid cloud APIs.

---

## 1.4 LLM Limitations

Even with a strong local model, the LLM still has limitations:

1. It can produce invalid JSON.
2. It can misunderstand ambiguous user messages.
3. It can hallucinate missing fields.
4. It may confuse similar financial actions.
5. It may be slower on weak hardware.
6. Vision extraction may fail on blurry receipts.
7. Financial advice should not be considered professional financial consulting.

Because of these limitations, AMMA does not allow the LLM to directly modify the database.  
All database-changing operations must pass through deterministic validation, confirmation, conflict checking, and tool execution.

---

# 2. Memory Management Comparison

The AMMA Agent needs memory because users often send incomplete financial requests or continue a previous action in the next message.

Example:

```text
User: Add lunch expense.
Agent: How much did it cost?
User: 300.
```

Without memory, the system cannot know that “300” belongs to the previous lunch expense request.

---

## 2.1 Compared Memory Options

| Memory Option | Description | Strengths | Weaknesses | Suitability for AMMA |
|---|---|---|---|---|
| **In-memory Python state** | Store memory directly in application variables. | Very simple, fast, easy to implement. | Lost when service restarts, not shared between containers, not suitable for production. | Not selected because AMMA is a containerized microservices project. |
| **PostgreSQL memory tables** | Store conversation state in relational tables. | Reliable, transactional, structured, already used in AMMA. | Less flexible for dynamic agent state, schema changes needed for new memory fields. | Good option, but not selected for dynamic agent memory. |
| **MongoDB session memory** | Store memory as flexible documents. | Flexible schema, good for conversation state, pending actions, conflict states, and dynamic fields. | Not ideal for semantic search by itself, long-term memory needs additional design. | **Selected for current implementation** because AMMA memory state is dynamic and session-based. |
| **Redis memory** | Store short-lived memory in fast key-value storage. | Very fast, good for temporary session cache, supports TTL. | Memory can disappear, not ideal as the main durable memory store. | Good for caching, but not selected as the main memory database. |
| **Vector database / RAG** | Store embeddings and retrieve semantically related memories/documents. | Good for long-term semantic retrieval, useful for knowledge files and user history. | More complex, requires embeddings, retrieval tuning, and evaluation. | Strong future improvement, but not necessary for the first implementation. |
| **Mem0** | Memory framework for LLM applications. | Designed for agent memory, can manage long-term personalized memory. | Adds dependency and complexity, needs integration and evaluation. | Good future option for long-term personalized memory. |
| **Zep** | Memory server for conversational AI. | Good conversation memory, summaries, and retrieval support. | Requires additional service setup and learning curve. | Good option, but heavier than current project needs. |
| **Graphiti / Graph-based memory** | Stores memory as temporal knowledge graph. | Good for relationships, evolving facts, and explainable long-term memory. | More complex than document/session memory; requires graph modeling. | Interesting future option, but not selected for the current version. |

---

## 2.2 Selected Memory Strategy

AMMA uses **MongoDB session memory** as the current memory management solution.

The memory stores:

- Session ID.
- Recent user messages.
- Recent assistant messages.
- Pending action.
- Missing fields.
- Confirmation state.
- Conflict state.
- Last extracted command.
- Workflow state needed for the next turn.

---

## 2.3 Why MongoDB Was Selected

MongoDB was selected because agent memory is not always fixed or relational.

For example, one request may need:

```json
{
  "pending_action": "create_expense",
  "missing_fields": ["amount"],
  "category": "Food"
}
```

Another request may need:

```json
{
  "conflict_state": {
    "type": "duplicate_expense",
    "similar_expense_id": 12
  }
}
```

A flexible document database is practical for this because the memory structure can evolve without changing SQL schemas every time the agent workflow changes.

---

## 2.4 Current Memory Flow

```text
User message
→ Memory Load Node
→ Load previous session state from MongoDB
→ Agent workflow continues with context
→ Tool execution or clarification happens
→ Memory Save Node
→ Updated state is saved back to MongoDB
```

---

## 2.5 Memory Shortcomings

The current memory system has limitations:

1. It is mainly short-term session memory.
2. It does not yet provide advanced long-term personalization.
3. It does not perform semantic search over old conversations.
4. It does not summarize long histories automatically.
5. It does not yet use embeddings.
6. It may become large if messages are not summarized or pruned.
7. It does not yet store user financial behavior patterns as reusable long-term memories.

---

## 2.6 Why Not Only RAG?

RAG is useful, but it is not enough for AMMA’s current workflow.

RAG is good for retrieving knowledge, but AMMA also needs operational memory such as:

- pending action
- confirmation state
- missing fields
- conflict state
- current workflow state

These are not just semantic documents. They are active workflow states.  
Therefore, MongoDB session memory is more suitable for the first implementation.

However, RAG can be added later to improve:

- long-term financial behavior retrieval
- user preference memory
- retrieval from financial rules
- retrieval from `.md` knowledge files
- historical advice generation

---

## 2.7 Future Upgraded Memory Design

A stronger future memory design can combine several layers:

| Memory Layer | Technology | Purpose |
|---|---|---|
| Working memory | MongoDB | Pending action, confirmation state, recent messages. |
| Cache memory | Redis | Fast temporary session cache and rate-limited states. |
| Semantic memory | Vector DB / RAG | Retrieve relevant old user history and financial rules. |
| Long-term profile memory | Mem0 or Zep | Store stable user preferences and repeated patterns. |
| Relationship memory | Graphiti | Store temporal relationships between user, categories, loans, and habits. |

---

## 2.8 Final Memory Choice

The selected current memory design is:

- **MongoDB** for session-based working memory.
- Possible future integration of **RAG/vector database** for semantic long-term memory.
- Possible future integration of **Mem0, Zep, or Graphiti** for advanced personalized memory.

This choice is justified because MongoDB is simple enough for the current project, flexible enough for agent workflow state, and easier to deploy inside the existing AMMA microservices environment.

---

# 3. Final Justification

AMMA uses a hybrid design:

- **LLMs** handle language understanding, routing, command extraction, image understanding, and advice generation.
- **Deterministic code** handles validation, confirmation, conflict detection, memory updates, and tool execution.
- **MongoDB memory** stores the active session state.
- **Ollama** allows local isolated LLM execution.
- **Docker** provides isolated service deployment.

This design is appropriate for a financial assistant because it combines natural language intelligence with controlled backend execution.
