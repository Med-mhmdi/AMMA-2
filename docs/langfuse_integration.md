# Langfuse Integration for AMMA Multi-Agent System

This document explains how Langfuse is integrated into the AMMA Multi-Agent System and how it is used during debugging, evaluation, and oral defense.

---

## 1. Purpose

AMMA is not only a normal backend service. It is a multi-agent LLM workflow.

A single user request can pass through several steps:

```text
User message
→ Agent API
→ LangGraph workflow
→ Memory loading
→ Supervisor routing
→ LLM command extraction
→ Validation
→ Conflict checking
→ Tool execution
→ Memory update
→ Final response
```

Because of this, normal logs are not enough.  
We need LLM-specific observability to understand:

- what prompt was sent to the model
- what the model returned
- which agent path was selected
- whether the model returned valid JSON
- how long the LLM call took
- whether the workflow failed before or after tool execution
- which request belongs to which user/session

Langfuse is used as the **LLM observability layer** for the AMMA Agent Service.

---

## 2. Why Langfuse Was Selected

Langfuse was selected because it is designed specifically for LLM applications and agentic workflows.

Compared with normal service monitoring tools:

| Tool | Main Purpose |
|---|---|
| Prometheus | Numeric metrics such as request count, latency, and errors. |
| Grafana | Dashboards for metrics and service health. |
| Loki | Centralized logs from services and containers. |
| Jaeger / OpenTelemetry | Distributed tracing across services. |
| Langfuse | LLM traces, prompts, completions, generations, tool calls, sessions, and agent debugging. |

AMMA can use Prometheus/Grafana for service-level monitoring, but Langfuse is more suitable for understanding what happens inside the multi-agent LLM workflow.

---

## 3. Position in the Architecture

Langfuse is integrated inside the **Agent Service**.

```text
React Frontend
→ API Gateway
→ Agent Service
   → Langfuse trace starts
   → LangGraph workflow span
   → Ollama LLM generations
   → Validation/tool execution metadata
   → Final response output
→ Expense / Loan / Analytics / Notification services
```

Langfuse does not replace the backend services.  
It only observes and records the agent workflow.

---

## 4. Files Added or Updated

The Langfuse integration adds or updates the following files:

```text
multi_agent_system/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── providers/
│   │   └── llm_provider.py
│   └── observability/
│       ├── __init__.py
│       └── langfuse_client.py
├── .env.langfuse.example
├── requirements.txt
└── docs/
    └── task_block_2_multiagent_system/
        └── langfuse_integration.md
```

---

## 5. Environment Variables

Langfuse is configured using environment variables.

Example:

```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_ENVIRONMENT=development
LANGFUSE_RELEASE=amma-multi-agent-v1
LANGFUSE_CAPTURE_INPUT_OUTPUT=true
LANGFUSE_MAX_PAYLOAD_CHARS=4000
```

If the Agent Service runs inside Docker and Langfuse also runs inside Docker, `localhost` should not be used from inside the Agent Service container.

In that case, use the Docker service name:

```env
LANGFUSE_HOST=http://langfuse-web:3000
```

---

## 6. Dependency

The project requires the Langfuse Python SDK.

In `requirements.txt`:

```txt
langfuse>=4.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Or rebuild Docker containers:

```bash
docker compose up --build
```

---

## 7. Langfuse Client

The file:

```text
app/observability/langfuse_client.py
```

contains helper functions for:

- creating a Langfuse client
- checking Langfuse status
- creating traces
- creating spans
- creating LLM generations
- updating traces
- flushing events during shutdown
- storing the current trace ID in request-local context

The client is defensive.  
If Langfuse is disabled, missing keys, unavailable, or incorrectly configured, the Agent Service continues running normally.

This is important because observability should not break the main application.

---

## 8. API-Level Tracing

Each call to:

```text
POST /agent/analyze
```

or:

```text
POST /agent/analyze/upload
```

creates one Langfuse trace.

The trace name is:

```text
AMMA Multi-Agent Request
```

The trace stores metadata such as:

- service name
- endpoint
- user ID
- session ID
- selected model
- selected vision model
- environment
- release version
- whether the request contains an image
- total latency
- final workflow status

---

## 9. Workflow Span

Inside each trace, the LangGraph workflow is recorded as a span:

```text
langgraph.workflow
```

This span represents the complete multi-agent workflow execution.

It records:

- session ID
- whether the request has text
- whether the request has an image
- selected intent
- selected next node
- validation result
- execution result
- errors
- total latency

This makes it possible to debug whether the request failed inside the graph or completed successfully.

---

## 10. LLM Generations

The LLM provider should record each Ollama call as a Langfuse generation.

Expected generation names:

```text
ollama.text_generation
ollama.vision_generation
```

Each generation can store:

- model name
- prompt/input
- model output
- latency
- parse success/failure
- JSON parsing errors
- agent type if available

This is the most important part for LLM observability because it shows exactly what the model received and returned.

---

## 11. Safe Payload Handling

The integration avoids sending very large payloads to Langfuse.

For example, receipt images are not sent as full base64 strings.

Instead, the trace stores:

```json
{
  "has_image_base64": true,
  "image_base64_length": 123456
}
```

The setting:

```env
LANGFUSE_MAX_PAYLOAD_CHARS=4000
```

limits long prompts and responses before sending them to Langfuse.

The setting:

```env
LANGFUSE_CAPTURE_INPUT_OUTPUT=false
```

can be used to hide prompts and outputs in sensitive environments.

---

## 12. Health and Debug Endpoint

The project exposes an endpoint to check Langfuse configuration:

```text
GET /agent/observability/langfuse
```

Example response:

```json
{
  "status": "ok",
  "langfuse": {
    "enabled": true,
    "available": true,
    "host": "http://localhost:3000",
    "environment": "development",
    "release": "amma-multi-agent-v1",
    "capture_input_output": true,
    "has_public_key": true,
    "has_secret_key": true
  }
}
```

The `/health` endpoint also includes Langfuse observability status.

---

## 13. What Langfuse Shows During Defense

During the oral defense, Langfuse can be used to show:

1. A user sends a message in the AMMA AI Assistant page.
2. The Agent Service creates a Langfuse trace.
3. The trace shows the full request metadata.
4. The workflow span shows the LangGraph execution.
5. LLM generations show prompts and responses.
6. The final trace output shows the final assistant response.
7. Errors or failed JSON parsing can be inspected directly.

Example demonstration request:

```text
Add 250 as food expense today.
```

Expected trace:

```text
AMMA Multi-Agent Request
└── langgraph.workflow
    ├── ollama.text_generation
    ├── validation
    ├── tool_execution
    └── final_response
```

Depending on the exact instrumentation, some steps may appear as spans or metadata rather than separate child spans.

---

## 14. Difference Between Langfuse and Prometheus/Grafana

Langfuse does not replace Prometheus or Grafana.

They solve different problems.

| Question | Better Tool |
|---|---|
| Is the service running? | Prometheus / health check |
| How many requests happened? | Prometheus |
| What is the average latency? | Prometheus / Grafana |
| What prompt was sent to the LLM? | Langfuse |
| What did the model return? | Langfuse |
| Why did the agent choose this route? | Langfuse |
| Did JSON parsing fail? | Langfuse |
| Which tool did the agent call? | Langfuse |
| Which container crashed? | Docker logs / Loki |

For AMMA, the best design is:

```text
Prometheus/Grafana = service-level observability
Langfuse = LLM and agent-level observability
```

---

## 15. Privacy Considerations

AMMA handles financial data, so Langfuse must be used carefully.

Safe metadata:

- session ID
- user ID
- route name
- action type
- model name
- latency
- validation status
- error type
- image length instead of full image

Sensitive information to avoid in production:

- passwords
- JWT tokens
- full financial history
- raw images
- private user details
- long unfiltered prompts containing sensitive data

For the defense/demo, `LANGFUSE_CAPTURE_INPUT_OUTPUT=true` is useful.  
For production, it can be changed to:

```env
LANGFUSE_CAPTURE_INPUT_OUTPUT=false
```

---

## 16. Failure Handling

The Langfuse integration is designed to be non-blocking.

If Langfuse is not configured or unavailable:

- the Agent Service still starts
- `/agent/analyze` still works
- Ollama calls still work
- backend tool execution still works
- only Langfuse traces are skipped

This is important because observability should support the system, not become a single point of failure.

---

## 17. Defense Explanation

Use this explanation during oral defense:

```text
I integrated Langfuse into the Agent Service as the LLM observability layer. 
Each AI assistant request creates a Langfuse trace. The trace records the user/session metadata, the LangGraph workflow execution, LLM generations, selected route, validation result, tool execution result, errors, and final response. 
This helps debug the multi-agent system because I can see not only that the service worked, but also what happened inside the LLM workflow.
Prometheus and Grafana are useful for general service metrics, while Langfuse is used specifically for LLM and agent tracing.
```

---

## 18. Current Limitation

The current integration focuses mainly on:

- request-level traces
- LangGraph workflow span
- LLM generation tracing
- final response metadata
- Langfuse health/status endpoint

Future improvements can include separate spans for every LangGraph node:

- `memory_load`
- `supervisor_router`
- `command_agent`
- `validation`
- `conflict_check`
- `tool_execution`
- `memory_update`
- `final_response`

This would make the trace even more detailed.

---

## 19. Conclusion

Langfuse improves AMMA by adding LLM-specific observability.

It allows the team to inspect the internal behavior of the multi-agent system, including prompts, model responses, route decisions, JSON parsing, workflow status, and errors.

This makes the system easier to debug, easier to evaluate, and easier to defend during the oral presentation.
