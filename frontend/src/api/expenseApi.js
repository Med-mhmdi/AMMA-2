import client from "./client";

const expenseApi = {
  getAll: () => client.get("/expenses"),

  create: (data) => client.post("/expenses", data),

  update: (id, data) => client.put(`/expenses/${id}`, data),

  remove: (id) => client.delete(`/expenses/${id}`),
};

export default expenseApi;