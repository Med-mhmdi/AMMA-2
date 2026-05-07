import client from "./client";

const budgetApi = {
  getByMonth: (year, month) => client.get(`/budgets?year=${year}&month=${month}`),

  update: (data) => client.put("/budgets", data),
};

export default budgetApi;