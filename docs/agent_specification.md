# AMMA Agent Specification

## 1. Agent Name

**AMMA Multi-Agent Financial Assistant**

AMMA stands for **AI Money Management Assistant**.  
The agent helps users manage personal financial data through natural language commands, financial analysis, receipt understanding, reminders, and notifications.

---

## 2. Purpose of the Agent

The AMMA Agent provides an intelligent assistant layer on top of the AMMA microservices platform.

Instead of forcing the user to manually navigate every page and form, the user can interact with the system using natural language, such as:

- “Add an expense of 250 for food.”
- “Show me my loans.”
- “Analyze my spending this month.”
- “Remind me if I am close to my budget limit.”
- “Extract the expense from this receipt image.”

The agent interprets the user message, identifies the intent, extracts structured data, validates the action, asks for missing information when necessary, and executes the correct backend operation only when it is safe to do so.

---

## 3. Main Objectives

The AMMA Agent has the following objectives:

1. Understand natural language financial requests.
2. Convert user messages into structured financial actions.
3. Support expense, income, category, loan, analytics, and notification workflows.
4. Use memory to continue incomplete user requests.
5. Ask clarification questions when required fields are missing.
6. Prevent unsafe or accidental database changes through validation and confirmation.
7. Detect possible duplicate or conflicting actions.
8. Provide financial advice based on user data.
9. Extract financial information from uploaded images or receipts.
10. Produce clear responses that are useful for non-technical users.

---

## 4. Target Users

The main target users are individuals who want to manage their personal finances more easily.

Typical users may want to:

- Track daily expenses.
- Record income.
- Manage borrowed or lent money.
- Monitor unpaid loans.
- View financial summaries.
- Receive warnings when budget usage is high.
- Get simple personalized financial advice.
- Use natural language instead of filling forms manually.

---

## 5. Agent Inputs

The AMMA Agent accepts several types of input.

### 5.1 Text Input

The user can send a natural language message through the AI Assistant page.

Examples:

```text
Add 500 as food expense.
Show my unpaid loans.
Create a category called Transport.
How much did I spend this month?
```

### 5.2 Image Input

The user can upload an image, such as a receipt or financial document.

The Vision Agent attempts to extract useful financial data from the image, such as:

- Amount
- Date
- Merchant or description
- Category
- Possible transaction type

### 5.3 Session Context

The agent can also use previous conversation context from memory.

Example:

```text
User: Add an expense for lunch.
Agent: How much did it cost?
User: 350.
```

The second message is understood using the previous pending action.

---

## 6. Agent Outputs

The agent can return different types of outputs depending on the situation.

### 6.1 Successful Execution Message

```text
Done. I added the food expense of 250.
```

### 6.2 Clarification Question

```text
What amount should I use for this expense?
```

### 6.3 Confirmation Request

```text
I found a possible expense: Food, 250. Do you want me to save it?
```

### 6.4 Conflict Warning

```text
A similar expense already exists. Do you still want to add this one?
```

### 6.5 Financial Advice

```text
Your food spending is high this month. You may need to reduce restaurant expenses for the rest of the month.
```

### 6.6 Error or Unsupported Request

```text
I could not process this request as a financial action. Please provide more details.
```

---

## 7. Supported Financial Actions

The Command Agent supports the following action types.

### 7.1 Expense Actions

| Action | Description |
|---|---|
| `create_expense` | Create a new expense or income transaction. |
| `update_expense` | Update an existing transaction. |
| `delete_expense` | Delete an existing transaction. |
| `list_expenses` | List expenses or income transactions. |

### 7.2 Category Actions

| Action | Description |
|---|---|
| `create_category` | Create a new expense or income category. |
| `update_category` | Update an existing category. |
| `delete_category` | Delete a category. |
| `list_categories` | List available categories. |

### 7.3 Loan Actions

| Action | Description |
|---|---|
| `create_loan` | Create a new loan record. |
| `update_loan` | Update loan information. |
| `update_loan_status` | Change loan status, such as paid, unpaid, or partially paid. |
| `delete_loan` | Delete a loan record. |
| `list_loans` | List loans. |

### 7.4 Analytics Actions

| Action | Description |
|---|---|
| `get_dashboard` | Get financial dashboard summary. |
| `get_category_summary` | Get spending grouped by category. |
| `get_budget_usage` | Check budget usage and warning level. |

### 7.5 Notification Actions

| Action | Description |
|---|---|
| `create_notification` | Create a warning, reminder, or recommendation notification. |
| `list_notifications` | List user notifications. |

### 7.6 Unknown Action

| Action | Description |
|---|---|
| `unknown` | Used when the user request cannot be mapped to a supported financial action. |

---

## 8. Multi-Agent Architecture

The AMMA Agent is implemented as a multi-agent system controlled by a LangGraph workflow.

The system is not a group of independent agents. Instead, all agents are integrated into one orchestrated workflow.

### 8.1 Main Agents and Nodes

| Component | Type | Responsibility |
|---|---|---|
| Memory Load Node | Deterministic node | Loads previous session memory before processing the request. |
| Supervisor Router Agent | LLM agent | Decides which agent path should handle the request. |
| Command Agent | LLM agent | Converts user text into a structured financial action. |
| Vision Agent | Vision LLM agent | Extracts financial information from images or receipts. |
| Financial Advisor Agent | LLM agent | Generates financial analysis and advice. |
| Recommendation Agent | LLM agent | Produces personalized recommendations. |
| Notification Agent | LLM agent | Decides whether advice should become a notification. |
| Clarification Agent | LLM agent | Asks for missing required information. |
| Tool Context Node | Deterministic node | Loads external financial data before validation or execution. |
| Validation Node | Deterministic node | Checks required fields and action safety. |
| Conflict Check Node | Deterministic node | Detects duplicates or conflicting actions. |
| Confirmation Handler | Deterministic node | Requires confirmation before mutating operations. |
| Tool Execution Node | Deterministic node | Calls backend services to execute approved actions. |
| Memory Save Node | Deterministic node | Saves updated memory and conversation state. |
| Final Response Node | Deterministic node | Builds the final response returned to the frontend. |

---

## 9. General Agent Flow

The normal text-command flow is:

```text
User message
→ Agent API Router
→ Memory Load Node
→ Supervisor Router Agent
→ Command Agent
→ Tool Context Node
→ Validation Node
→ Conflict Check Node
→ Confirmation Handler
→ Tool Execution Node
→ Memory Save Node
→ Final Response Node
→ Frontend response
```

For image input, the flow becomes:

```text
User image
→ Agent API Router
→ Memory Load Node
→ Supervisor Router Agent
→ Vision Agent
→ Command Agent or Clarification Agent
→ Validation Node
→ Confirmation Handler
→ Tool Execution Node
→ Memory Save Node
→ Final Response Node
```

For advice requests, the flow becomes:

```text
User question
→ Agent API Router
→ Memory Load Node
→ Supervisor Router Agent
→ Tool Context Node
→ Financial Advisor Agent
→ Notification Agent
→ Memory Save Node
→ Final Response Node
```

---

## 10. LLM Usage

The AMMA Agent uses an LLM for language understanding and reasoning tasks.

The LLM is used for:

- Intent classification.
- Routing decisions.
- Extracting structured financial commands.
- Understanding incomplete user messages.
- Generating clarification questions.
- Analyzing financial context.
- Generating financial advice.
- Extracting data from images through a vision model.
- Deciding whether a recommendation should become a notification.

The LLM is **not** directly trusted to modify the database.

All database-changing operations pass through deterministic validation, confirmation, conflict checking, and tool execution.

---

## 11. Deterministic Logic

Several parts of the system are intentionally hardcoded or deterministic.

This is important because financial systems require correctness and safety.

Deterministic logic is used for:

- Required field validation.
- Checking action type.
- Checking transaction amount format.
- Checking whether an operation changes the database.
- Asking for confirmation before create, update, or delete actions.
- Detecting possible duplicates.
- Saving or clearing memory state.
- Calling exact backend service endpoints.
- Building the final response structure.

This hybrid design allows the LLM to handle flexible language while deterministic code controls safety-critical execution.

---

## 12. Memory Management

The AMMA Agent uses memory to support multi-turn conversations.

### 12.1 Short-Term Memory

Short-term memory stores information related to the current session.

It may include:

- Recent user messages.
- Recent assistant messages.
- Current session ID.
- Pending action.
- Missing fields.
- Confirmation state.
- Conflict state.
- Last extracted command.

Example:

```text
User: Add lunch expense.
Agent: How much did it cost?
User: 300.
```

The system uses short-term memory to understand that “300” completes the previous lunch expense request.

### 12.2 Memory Storage

The current implementation uses **MongoDB** as the memory store.

MongoDB stores flexible session documents, which is useful because agent memory can contain dynamic fields such as pending actions, messages, and conflict states.

### 12.3 Current Memory Limitation

The current memory system is mainly session-based working memory.  
It is useful for short conversations and pending actions, but it does not yet provide advanced long-term personalization.

Future improvements may include:

- Long-term user preference memory.
- Financial behavior summaries.
- Vector-based semantic retrieval.
- RAG over user financial history.
- Memory frameworks such as Mem0, Zep, or Graphiti.

---

## 13. Tools and Skills

In AMMA, a skill is an operation that the agent can perform through backend services.

The agent does not directly manipulate the database from the LLM output.  
Instead, it calls controlled tools.

### 13.1 Expense Skills

- Create expense.
- Update expense.
- Delete expense.
- List expenses.
- Create category.
- Update category.
- Delete category.
- List categories.

### 13.2 Loan Skills

- Create loan.
- Update loan.
- Delete loan.
- Update loan status.
- List loans.

### 13.3 Analytics Skills

- Get dashboard summary.
- Analyze spending by category.
- Check budget usage.
- Generate financial context.

### 13.4 Notification Skills

- Create budget warning.
- Create reminder.
- Create financial recommendation notification.
- List notifications.

### 13.5 Vision Skill

- Analyze receipt image.
- Extract possible amount, category, date, and description.

---

## 14. System Prompts

Each LLM-based agent uses a focused system prompt.

The purpose of system prompts is to restrict each agent to a specific responsibility.

### 14.1 Supervisor Router Agent Prompt

The Supervisor Router Agent decides which path should handle the user request.

It classifies the request into categories such as:

- financial command
- vision request
- financial advice
- notification request
- clarification
- unknown

### 14.2 Command Agent Prompt

The Command Agent converts natural language into structured JSON.

It must return a supported action such as:

```json
{
  "action": "create_expense",
  "amount": 250,
  "category": "Food",
  "description": "Lunch",
  "type": "outcome"
}
```

### 14.3 Vision Agent Prompt

The Vision Agent extracts structured financial information from an image.

### 14.4 Advisor Agent Prompt

The Advisor Agent analyzes financial data and returns useful advice.

### 14.5 Clarification Agent Prompt

The Clarification Agent asks the user for missing information without executing the action.

---

## 15. Data Safety Rules

The AMMA Agent follows strict safety rules.

1. The LLM cannot directly write to the database.
2. Mutating actions require validation.
3. Important mutating actions require confirmation.
4. Missing required fields trigger clarification.
5. Duplicate or suspicious actions trigger conflict handling.
6. Tool execution uses backend APIs, not raw LLM-generated database queries.
7. The final response must reflect the real execution result, not only the LLM intention.

---

## 16. Isolation and Deployment

The AMMA platform is designed to run in an isolated environment using Docker.

Each service can run inside its own container:

- API Gateway container
- Auth Service container
- Expense Service container
- Loan Service container
- Analytics Service container
- Agent Service container
- Notification Service container
- PostgreSQL containers
- MongoDB container
- Ollama runtime container

Docker isolation was selected because it provides:

- Reproducible execution.
- Service-level separation.
- Easier local deployment.
- Independent scaling of services.
- Clear boundaries between databases and services.
- Safer execution than running all components directly on the host machine.

Compared with a full virtual machine, Docker is lighter and easier to use for a microservices-based student project.

---

## 17. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| API Gateway | FastAPI |
| Backend Services | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Runtime | Ollama |
| Text LLM | Qwen 2.5 7B  |
| Vision LLM | LLaVA |
| Structured Databases | PostgreSQL |
| Agent Memory | MongoDB |
| Deployment | Docker / Docker Compose |
| Communication | HTTP APIs |
| Observability | Logs, metrics, traces, alerts |

---

## 18. Evaluation Criteria

The AMMA Agent can be evaluated using two levels of evaluation:

1. LLM evaluation.
2. Agentic system evaluation.

### 18.1 LLM Evaluation

The LLM can be evaluated using:

- Intent classification accuracy.
- JSON validity.
- Field extraction accuracy.
- Ability to handle incomplete messages.
- Ability to avoid unsupported actions.
- Quality of financial advice.
- Receipt extraction quality for image input.

Example test:

```text
Input: Add 250 for food today.
Expected action: create_expense
Expected amount: 250
Expected category: Food
Expected type: outcome
```

### 18.2 Agentic System Evaluation

The full agentic system can be evaluated using:

- Tool execution success rate.
- Number of successful end-to-end tasks.
- Clarification success rate.
- Confirmation correctness.
- Conflict detection accuracy.
- Average response time.
- Error rate.
- Number of failed tool calls.
- Memory continuation accuracy.
- User satisfaction during manual testing.

---

## 19. Observability

The AMMA Agent should be monitored using metrics, logs, traces, and alerts.

### 19.1 Logs

Logs should record:

- Request received.
- Selected intent.
- Selected agent path.
- Validation result.
- Tool execution result.
- Errors and exceptions.

### 19.2 Metrics

Useful metrics include:

- Number of agent requests.
- Average response time.
- LLM latency.
- Tool execution success rate.
- Validation failure count.
- Clarification count.
- Confirmation count.
- Conflict detection count.
- Error rate.

### 19.3 Traces

Traces are useful because the agent workflow has multiple steps.

A trace can show:

```text
API Router
→ Memory Load
→ Supervisor Router
→ Command Agent
→ Validation
→ Tool Execution
→ Memory Save
→ Final Response
```

### 19.4 Alerts

Possible alerts include:

- Agent Service is down.
- Ollama runtime is unavailable.
- LLM response time is too high.
- Tool execution failure rate is high.
- Database connection failure.
- Too many validation failures.
- Too many unhandled errors.

---

## 20. Limitations

The current AMMA Agent has some limitations.

1. Long-term memory is limited.
2. The agent depends on the quality of the selected local LLM.
3. Small local models may produce invalid JSON.
4. Vision extraction can fail with unclear receipt images.
5. Financial advice is basic and should not be treated as professional financial consulting.
6. Advanced RAG is not fully implemented yet.
7. Observability can be improved with a complete Prometheus, Grafana, Loki, and Jaeger setup.
8. More automated evaluation tests should be added.

---

## 21. Future Improvements

Future improvements include:

1. Add long-term user preference memory.
2. Add vector search for semantic memory retrieval.
3. Add RAG over user financial history and financial rules.
4. Add evaluation datasets for each supported action.
5. Add automatic regression tests for prompts.
6. Improve duplicate detection.
7. Improve receipt extraction accuracy.
8. Add voice input.
9. Add stronger observability dashboards.
10. Add budget prediction and automatic notification logic.

---

## 22. Conclusion

The AMMA Agent is a multi-agent financial assistant integrated into the AMMA microservices platform.

The system uses LLM agents for flexible language understanding, routing, command extraction, vision analysis, advice, and clarification. At the same time, deterministic logic controls validation, confirmation, conflict checking, memory updates, and tool execution.

This architecture provides a balance between intelligence and safety. The LLM improves user interaction, while deterministic backend logic protects the financial data from unsafe or hallucinated actions.
