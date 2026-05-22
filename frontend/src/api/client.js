const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 180000; // 3 minutes for local Ollama/AI calls

function getAuthHeaders() {
  const token = localStorage.getItem("token");

  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
      signal: controller.signal,
      ...options,
    });

    if (!response.ok) {
      let errorMessage = "Request failed";

      try {
        const errorData = await response.json();

        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail
            .map((item) => item.msg)
            .join(" | ");
        } else {
          errorMessage =
            errorData.final_response?.message ||
            errorData.result?.message ||
            errorData.detail ||
            errorData.message ||
            errorMessage;
        }
      } catch {
        // fallback if response is not JSON
      }

      throw new Error(errorMessage);
    }

    const text = await response.text();
    return text ? JSON.parse(text) : null;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "The AI request took too long. Local Ollama may still be processing."
      );
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

const client = {
  get: (path) => request(path, { method: "GET" }),

  post: (path, body) =>
    request(path, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  put: (path, body) =>
    request(path, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  delete: (path) =>
    request(path, {
      method: "DELETE",
    }),
};

export default client;