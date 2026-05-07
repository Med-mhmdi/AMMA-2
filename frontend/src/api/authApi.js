import client from "./client";

const authApi = {
  login: (data) => client.post("/auth/login", data),

  register: (data) => client.post("/auth/register", data),
};

export default authApi;