import client from "./client";

const categoryApi = {
  getAll: () => client.get("/categories"),
  create: (data) => client.post("/categories", data),
  update: (id, data) => client.put(`/categories/${id}`, data),
  remove: (id) => client.delete(`/categories/${id}`),
};

export default categoryApi;