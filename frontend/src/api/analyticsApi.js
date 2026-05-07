import client from "./client";

const analyticsApi = {
  getDashboard: (year, month, period) =>
    client.get(`/analytics/dashboard?year=${year}&month=${month}&period=${period}`),

  getCategories: (year, month, period, transactionType) =>
    client.get(
      `/analytics/categories?year=${year}&month=${month}&period=${period}&transaction_type=${transactionType}`
    ),

  getDaily: (year, month) =>
    client.get(`/analytics/daily?year=${year}&month=${month}`),

  getForecast: (year, month) =>
    client.get(`/analytics/forecast?year=${year}&month=${month}`),
};

export default analyticsApi;