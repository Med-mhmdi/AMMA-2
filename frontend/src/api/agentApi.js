import client from "./client";

const agentApi = {
  sendMessage: (data) => client.post("/agent/analyze", data),
};

export default agentApi;