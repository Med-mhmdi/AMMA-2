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

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      resolve(reader.result);
    };

    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function formatBotMessage(payload) {
  if (!payload) {
    return "I could not read the assistant response.";
  }

  const unwrapped = unwrapPayload(payload);

  // Main AMMA backend response shapes.
  if (unwrapped.final_response?.message) {
    return unwrapped.final_response.message;
  }

  if (unwrapped.result?.message) {
    return unwrapped.result.message;
  }

  if (unwrapped.result?.final_response?.message) {
    return unwrapped.result.final_response.message;
  }

  if (unwrapped.clarification_result?.message) {
    return unwrapped.clarification_result.message;
  }

  if (unwrapped.validation?.question) {
    return unwrapped.validation.question;
  }

  const result = unwrapped.result || unwrapped;
  const debug = unwrapped.debug || {};
  const execution =
    result.execution ||
    unwrapped.execution_result ||
    result.execution_result ||
    debug.execution_result ||
    {};

  const actionName =
    result.action?.action ||
    debug.extracted_action?.action ||
    execution.action ||
    result.final_response?.action ||
    unwrapped.final_response?.action ||
    unwrapped.current_action?.action;

  if (actionName === "list_categories") {
    const categories = findArray(
      execution.categories,
      result.categories,
      result.data,
      debug.tool_context?.categories,
      unwrapped.final_response?.matches
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
      debug.tool_context?.expenses,
      unwrapped.final_response?.matches
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
      debug.tool_context?.loans,
      unwrapped.final_response?.matches
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

  if (result.type === "conflict_resolution" || unwrapped.final_response?.type === "conflict_resolution") {
    return result.message || unwrapped.final_response?.message || "A possible duplicate was found.";
  }

  if (result.type === "confirmation" || unwrapped.final_response?.type === "confirmation") {
    return result.message || unwrapped.final_response?.message || "Please confirm, or correct anything.";
  }

  if (result.message) {
    return result.message;
  }

  if (execution.message) {
    return execution.message;
  }

  if (unwrapped.message) {
    return unwrapped.message;
  }

  return "Done.";
}

export default function AiAssistantPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi, I am AMMA. You can ask me to add expenses, list loans, check categories, analyze spending, or upload a receipt image.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedImagePreview, setSelectedImagePreview] = useState(null);

  const bottomRef = useRef(null);

  const sessionId = getSessionId();
  const userId = getUserId();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const clearSelectedImage = () => {
    if (selectedImagePreview) {
      URL.revokeObjectURL(selectedImagePreview);
    }

    setSelectedImage(null);
    setSelectedImagePreview(null);
  };

  const handleImageChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      alert("Please select an image file.");
      event.target.value = "";
      return;
    }

    if (selectedImagePreview) {
      URL.revokeObjectURL(selectedImagePreview);
    }

    setSelectedImage(file);
    setSelectedImagePreview(URL.createObjectURL(file));

    // Allows choosing the same image again later.
    event.target.value = "";
  };

  const sendMessage = async () => {
    const cleanMessage = input.trim();

    if ((!cleanMessage && !selectedImage) || loading) {
      return;
    }

    const userMessageContent = cleanMessage || "Analyze this receipt image";
    const imagePreviewForMessage = selectedImagePreview;

    setInput("");

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: userMessageContent,
        imagePreview: imagePreviewForMessage,
      },
    ]);

    try {
      setLoading(true);

      let imageBase64 = null;

      if (selectedImage) {
        imageBase64 = await fileToBase64(selectedImage);
      }

      const response = await agentApi.sendMessage({
        user_id: userId,
        session_id: sessionId,
        message: userMessageContent,
        image_base64: imageBase64,
        image_url: null,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: formatBotMessage(response),
          raw: response,
        },
      ]);

      clearSelectedImage();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            err?.response?.data?.final_response?.message ||
            err?.response?.data?.result?.message ||
            err?.response?.data?.detail ||
            err.message ||
            "Failed to contact AMMA assistant.",
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
              detect duplicates, ask confirmation, read receipt images, and
              explain your finances.
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
              disabled={loading}
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

                {message.imagePreview && (
                  <img
                    src={message.imagePreview}
                    alt="Uploaded receipt"
                    className="ai-message-image"
                  />
                )}

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

        {selectedImagePreview && (
          <div className="ai-selected-image-preview">
            <img src={selectedImagePreview} alt="Selected receipt" />

            <div className="ai-selected-image-info">
              <strong>{selectedImage?.name || "Selected image"}</strong>
              <span>Ready to send as receipt/image input</span>
            </div>

            <button
              type="button"
              className="ai-remove-image-btn"
              onClick={clearSelectedImage}
              disabled={loading}
            >
              Remove
            </button>
          </div>
        )}

        <div className="ai-input-panel">
          <label className="ai-upload-btn">
            <span>📎</span>
            <span>Image</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              hidden
              disabled={loading}
            />
          </label>

          <textarea
            value={input}
            placeholder="Example: add coffee 250 food, or upload a receipt"
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          <button
            type="button"
            className="btn btn-primary ai-send-btn"
            onClick={sendMessage}
            disabled={loading || (!input.trim() && !selectedImage)}
          >
            <span className="btn-icon">➤</span>
            <span className="btn-label">{loading ? "Sending" : "Send"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}