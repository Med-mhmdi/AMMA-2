import { useEffect, useMemo, useState } from "react";
import analyticsApi from "../api/analyticsApi";
import budgetApi from "../api/budgetApi";
import PageHeader from "../components/PageHeader";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

import "../styles/analytics.css";

const COLORS = ["#3fa9f5", "#ff7a18", "#28c76f", "#00cfe8", "#b78cff", "#ff5757"];
const now = new Date();

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [period, setPeriod] = useState("monthly");
  const [categoryType, setCategoryType] = useState("outcome");
  const [expandedChart, setExpandedChart] = useState(null);

  const [dashboard, setDashboard] = useState({});
  const [categories, setCategories] = useState([]);
  const [daily, setDaily] = useState([]);
  const [budgetInput, setBudgetInput] = useState("");

  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(now.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(now.getMonth() + 1);

  const toggleChart = (chartName) => {
    setExpandedChart(expandedChart === chartName ? null : chartName);
  };

  const loadAnalytics = async () => {
    try {
      setLoading(true);

      const dash = await analyticsApi.getDashboard(selectedYear, selectedMonth, period);
      const cats = await analyticsApi.getCategories(
        selectedYear,
        selectedMonth,
        period,
        categoryType
      );
      const dailyData = await analyticsApi.getDaily(selectedYear, selectedMonth);

      setDashboard(dash || {});
      setCategories(Array.isArray(cats) ? cats : []);
      setDaily(Array.isArray(dailyData) ? dailyData : []);
      setBudgetInput(String(dash?.budget_status?.budget || 0));
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [selectedYear, selectedMonth, period, categoryType]);

  const totalIncome = dashboard.total_income ?? 0;
  const totalExpenses = dashboard.total_expense ?? 0;
  const balance = dashboard.balance ?? totalIncome - totalExpenses;
  const monthlyData = dashboard.monthly || [];

  const budgetStatusData = dashboard.budget_status || {};
  const rawBudgetPercent = budgetStatusData.percent_used ?? 0;
  const budgetPercentForBar = budgetStatusData.bar_percent ?? 0;
  const budgetLeft = budgetStatusData.budget_left ?? 0;
  const budgetStatus = budgetStatusData.status ?? "safe";
  const budgetMessage = budgetStatusData.message ?? "";
  const showBudgetWarning = budgetMessage !== "";

  const categoriesWithPercent = useMemo(() => {
    const total = categories.reduce((sum, item) => sum + Number(item.amount || 0), 0);

    return categories
      .map((item) => ({
        ...item,
        percent: total > 0 ? ((Number(item.amount || 0) / total) * 100).toFixed(1) : 0,
      }))
      .sort((a, b) => Number(b.amount) - Number(a.amount));
  }, [categories]);

  const updateBudget = async () => {
    try {
      await budgetApi.update({
        year: selectedYear,
        month: selectedMonth,
        amount: Number(budgetInput || 0),
      });

      await loadAnalytics();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to update budget");
    }
  };

  if (loading) {
    return (
      <div className="analytics-page">
        <p className="analytics-loading">Loading analytics...</p>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <PageHeader title="Analytics" />

      <div className="analytics-toolbar">
        <div className="analytics-tabs">
          <button
            className={activeTab === "overview" ? "active" : ""}
            onClick={() => setActiveTab("overview")}
          >
            Overview
          </button>

          <button
            className={activeTab === "categories" ? "active" : ""}
            onClick={() => setActiveTab("categories")}
          >
            Categories
          </button>

          <button
            className={activeTab === "daily" ? "active" : ""}
            onClick={() => setActiveTab("daily")}
          >
            Daily Trend
          </button>

          <button
            className={activeTab === "loans" ? "active" : ""}
            onClick={() => setActiveTab("loans")}
          >
            Loan Summary
          </button>
        </div>

        <div className="analytics-filters">
          <input
            type="number"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
          />

          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(Number(e.target.value))}
          >
            <option value={1}>January</option>
            <option value={2}>February</option>
            <option value={3}>March</option>
            <option value={4}>April</option>
            <option value={5}>May</option>
            <option value={6}>June</option>
            <option value={7}>July</option>
            <option value={8}>August</option>
            <option value={9}>September</option>
            <option value={10}>October</option>
            <option value={11}>November</option>
            <option value={12}>December</option>
          </select>
        </div>
      </div>

      {activeTab === "overview" && (
        <div className="analytics-content">
          <div className="analytics-overview-layout">
            <div className="period-switch vertical">
              <button
                className={period === "monthly" ? "active" : ""}
                onClick={() => setPeriod("monthly")}
              >
                Monthly
              </button>

              <button
                className={period === "yearly" ? "active" : ""}
                onClick={() => setPeriod("yearly")}
              >
                Yearly
              </button>
            </div>

            <div className="analytics-summary compact">
              <div className="analytics-card">
                <h3>Total Income</h3>
                <p>{totalIncome}</p>
              </div>

              <div className="analytics-card">
                <h3>Total Expenses</h3>
                <p>{totalExpenses}</p>
              </div>

              <div className="analytics-card">
                <h3>Balance</h3>
                <p className={balance >= 0 ? "positive-value" : "negative-value"}>
                  {balance}
                </p>
              </div>

              <div className="analytics-card">
                <h3>Active Loans</h3>
                <p>{dashboard.active_loan_count ?? 0}</p>
              </div>
            </div>
          </div>

          <div className="budget-row">
            <div className="budget-card">
              <div className="budget-header">
                <h2>Budget Progress</h2>

                {showBudgetWarning && (
                  <div className={`budget-warning-banner ${budgetStatus}`}>
                    {budgetMessage}
                  </div>
                )}

                <p>
                  Used: <strong>{Number(rawBudgetPercent).toFixed(1)}%</strong>
                </p>
              </div>

              <div className="budget-bar">
                <div
                  className={`budget-fill ${budgetStatus}`}
                  style={{ width: `${budgetPercentForBar}%` }}
                />
              </div>

              <div className="budget-left-text">
                {budgetLeft >= 0 ? (
                  <>
                    Left to use: <strong>{budgetLeft}</strong>
                  </>
                ) : (
                  <>
                    Over budget by: <strong>{Math.abs(budgetLeft)}</strong>
                  </>
                )}
              </div>
            </div>

            <div className="budget-update-card">
              <label>Monthly Budget</label>
              <div className="budget-update-row">
                <input
                  type="number"
                  value={budgetInput}
                  onChange={(e) => setBudgetInput(e.target.value)}
                />
                <button onClick={updateBudget}>Update</button>
              </div>
            </div>
          </div>

          <div
            className={`analytics-chart overview-chart ${
              expandedChart === "income" ? "chart-expanded" : ""
            }`}
          >
            <button className="chart-expand-btn" onClick={() => toggleChart("income")}>
              {expandedChart === "income" ? "✕" : "⛶"}
            </button>

            <h2>Income vs Expenses for {selectedYear}</h2>

            <div className="chart-body">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2f2f2f" />
                  <XAxis dataKey="month" stroke="#d0d0d0" />
                  <YAxis stroke="#d0d0d0" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="income" fill="#28c76f" />
                  <Bar dataKey="expense" fill="#ff5757" />
                  <Bar dataKey="balance" fill="#3fa9f5" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === "categories" && (
        <div className="analytics-content">
          <div className="category-options">
            <div className="period-switch">
              <button
                className={period === "monthly" ? "active" : ""}
                onClick={() => setPeriod("monthly")}
              >
                Monthly
              </button>

              <button
                className={period === "yearly" ? "active" : ""}
                onClick={() => setPeriod("yearly")}
              >
                Yearly
              </button>
            </div>

            <div className="period-switch">
              <button
                className={categoryType === "outcome" ? "active" : ""}
                onClick={() => setCategoryType("outcome")}
              >
                Outcome
              </button>

              <button
                className={categoryType === "income" ? "active" : ""}
                onClick={() => setCategoryType("income")}
              >
                Income
              </button>
            </div>
          </div>

          <div className="analytics-grid two">
            <div className="analytics-chart">
              <h2>{categoryType === "income" ? "Income" : "Outcome"} Category Breakdown</h2>

              {categories.length > 0 ? (
                <ResponsiveContainer width="100%" height={310}>
                  <PieChart>
                    <Pie
                      data={categories}
                      dataKey="amount"
                      nameKey="category"
                      outerRadius={105}
                      label
                    >
                      {categories.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>

                    <Legend />
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="empty-message">No category data available.</p>
              )}
            </div>

            <div className="analytics-chart top-categories-chart">
              <h2>Top Categories</h2>

              {categoriesWithPercent.length > 0 ? (
                <table className="analytics-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Amount</th>
                      <th>Percent</th>
                    </tr>
                  </thead>

                  <tbody>
                    {categoriesWithPercent.map((item) => (
                      <tr key={item.category}>
                        <td>{item.category}</td>
                        <td>{item.amount}</td>
                        <td>{item.percent}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="empty-message">No category data available.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === "daily" && (
        <div className="analytics-content">
          <div
            className={`analytics-chart daily-chart ${
              expandedChart === "daily" ? "chart-expanded" : ""
            }`}
          >
            <button className="chart-expand-btn" onClick={() => toggleChart("daily")}>
              {expandedChart === "daily" ? "✕" : "⛶"}
            </button>

            <h2>Daily Spending Trend</h2>

            {daily.length > 0 ? (
              <div className="chart-body">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2f2f2f" />
                    <XAxis dataKey="day" stroke="#d0d0d0" />
                    <YAxis stroke="#d0d0d0" />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="expense" stroke="#ff5757" strokeWidth={3} />
                    <Line type="monotone" dataKey="income" stroke="#28c76f" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="empty-message">No daily data for selected month.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "loans" && (
        <div className="analytics-content">
          <div className="analytics-loan-page">
            <div className="analytics-summary compact loan-cards">
              <div className="analytics-card">
                <h3>Total Borrowed</h3>
                <p>{dashboard.borrowed_total ?? 0}</p>
              </div>

              <div className="analytics-card">
                <h3>Total Lent</h3>
                <p>{dashboard.lent_total ?? 0}</p>
              </div>

              <div className="analytics-card">
                <h3>Active Borrowed</h3>
                <p>{dashboard.active_borrowed ?? 0}</p>
              </div>

              <div className="analytics-card">
                <h3>Active Lent</h3>
                <p>{dashboard.active_lent ?? 0}</p>
              </div>
            </div>

            <div className="loan-summary-grid">
              <div className="analytics-chart loan-balance-card">
                <h2>Loan Balance</h2>

                <div className="loan-summary-result">
                  <p className={(dashboard.loan_balance ?? 0) >= 0 ? "positive-value" : "negative-value"}>
                    {dashboard.loan_balance ?? 0}
                  </p>

                  <h3>{dashboard.loan_status ?? "Balanced"}</h3>

                  <span>
                    This compares remaining active borrowed money against remaining active lent money.
                  </span>
                </div>
              </div>

              <div className="analytics-chart active-loans-card">
                <h2>Active Loan People</h2>

                {dashboard.active_people && dashboard.active_people.length > 0 ? (
                  <table className="analytics-table">
                    <thead>
                      <tr>
                        <th>Person</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Left To Pay</th>
                      </tr>
                    </thead>

                    <tbody>
                      {dashboard.active_people.map((item, index) => (
                        <tr key={index}>
                          <td>{item.person_name}</td>
                          <td>{item.type}</td>
                          <td>{item.status}</td>
                          <td>{item.remaining_amount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="empty-message">No active loans found.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}