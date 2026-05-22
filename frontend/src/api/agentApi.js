import client from "./client";

const agentApi = {
  async sendMessage(data) {
    const response = await client.post("/agent/analyze", data);

    // Supports Axios-style response: { data: ... }
    // and custom-client response: direct JSON object.
    return response?.data || response;
  },
};

export default agentApi;