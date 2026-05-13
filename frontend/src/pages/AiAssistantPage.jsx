import { useEffect, useRef, useState } from "react";
import PageHeader from "../components/PageHeader";
import agentApi from "../api/agentApi";
import "../styles/aiAssistant.css";

function getSessionId() {
  const key = "amma_ai_session_id";
  const existing = localStorage.getItem(key);

  if (existing) {
    return existing;
  }

  const created = `web-session-${Date.now()}`;
  localStorage.setItem(key, created);
  return created;
}

function getUserId() {
  const storedUserId = localStorage.getItem("user_id");
  return storedUserId ? Number(storedUserId) : 1;
}

function unwrapPayload(payload) {
  // Supports both Axios response shape and direct fetch response shape.
  return payload?.data || payload;
}

function formatList(title, items, formatter) {
  if (!Array.isArray(items) || items.length === 0) {
    return `${title}\nNo records found.`;
  }

  return `${title}\n${items.map(formatter).join("\n")}`;
}

function findArray(...values) {
  return values.find((value) => Array.isArray(value));
}

function formatBotMessage(payload) {
  if (!payload) {
    return "I could not read the assistant response.";
  }

  const unwrapped = unwrapPayload(payload);
  const result = unwrapped.result || unwrapped;
  const debug = unwrapped.debug || {};
  const execution = result.execution || debug.execution_result || {};

  const actionName =
    result.action?.action ||
    debug.extracted_action?.action ||
    execution.action;

  if (actionName === "list_categories") {
    const categories = findArray(
      execution.categories,
      result.categories,
      result.data,
      debug.tool_context?.categories
    );

    if (categories) {
      return formatList(
        "Categories:",
        categories,
        (item) => `- #${item.id} ${item.name || item.category || "Unnamed"}`
      );
    }
  }

  if (actionName === "list_expenses") {
    const expenses = findArray(
      execution.expenses,
      execution.data,
      result.expenses,
      result.data,
      debug.tool_context?.expenses
    );

    if (expenses) {
      return formatList(
        "Expenses:",
        expenses,
        (item) =>
          `- #${item.id} ${item.description || "Expense"} | ${item.amount} | ${
            item.category_name || item.category || "No category"
          } | ${item.transaction_date || item.date || ""}`
      );
    }
  }

  if (actionName === "list_loans") {
    const loans = findArray(
      execution.loans,
      execution.data,
      result.loans,
      result.data,
      debug.tool_context?.loans
    );

    if (loans) {
      return formatList(
        "Loans:",
        loans,
        (item) =>
          `- #${item.id} ${item.person_name || item.person || "Unknown"} | ${
            item.amount
          } | ${item.type || ""} | ${item.status || ""}`
      );
    }
  }

  if (result.type === "conflict_resolution") {
    return result.message || "A possible duplicate was found.";
  }

  if (result.type === "confirmation") {
    return result.message || "Please confirm, or correct anything.";
  }

  if (result.message) {
    return result.message;
  }

  if (execution.message) {
    return execution.message;
  }

  return "Done.";
}

export default function AiAssistantPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi, I am AMMA. You can ask me to add expenses, list loans, check categories, analyze spending, or manage financial actions.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const sessionId = getSessionId();
  const userId = getUserId();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    const cleanMessage = input.trim();

    if (!cleanMessage || loading) {
      return;
    }

    setInput("");

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: cleanMessage,
      },
    ]);

    try {
      setLoading(true);

      const response = await agentApi.sendMessage({
        user_id: userId,
        session_id: sessionId,
        message: cleanMessage,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: formatBotMessage(response),
          raw: response,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err.message || "Failed to contact AMMA assistant.",
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const quickMessages = [
    "add tea 100 food",
    "show my expenses",
    "show my categories",
    "analyze my spending",
  ];

  return (
    <div className="ai-page">
      <PageHeader title="AI Assistant" />

      <div className="ai-chat-shell">
        <div className="ai-chat-header">
          <div>
            <h2>AMMA Chat</h2>
            <p>
              Talk naturally with your money assistant. It can create expenses,
              detect duplicates, ask confirmation, and explain your finances.
            </p>
          </div>

          <span className="ai-session-badge">Session active</span>
        </div>

        <div className="ai-quick-row">
          {quickMessages.map((item) => (
            <button
              key={item}
              type="button"
              className="ai-quick-btn"
              onClick={() => setInput(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="ai-chat-window">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`ai-message-row ${
                message.role === "user" ? "user" : "assistant"
              }`}
            >
              <div
                className={`ai-message-bubble ${
                  message.isError ? "error" : ""
                }`}
              >
                <div className="ai-message-role">
                  {message.role === "user" ? "You" : "AMMA"}
                </div>

                <div className="ai-message-content">{message.content}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="ai-message-row assistant">
              <div className="ai-message-bubble">
                <div className="ai-message-role">AMMA</div>
                <div className="ai-message-content">Thinking...</div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="ai-input-panel">
          <textarea
            value={input}
            placeholder="Example: add coffee 250 food"
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
          />

          <button
            type="button"
            className="btn btn-primary ai-send-btn"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            <span className="btn-icon">➤</span>
            <span className="btn-label">{loading ? "Sending" : "Send"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}