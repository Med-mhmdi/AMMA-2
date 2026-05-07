import client from "./client";

const loanApi = {
  getAll: () => client.get("/loans"),

  create: (data) => client.post("/loans", data),

  update: (id, data) => client.put(`/loans/${id}`, data),

  remove: (id) => client.delete(`/loans/${id}`),
};

export default loanApi;