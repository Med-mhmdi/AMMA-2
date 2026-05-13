import { Routes, Route } from "react-router-dom";

import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import DashboardPage from "../pages/DashboardPage";
import ExpensesPage from "../pages/ExpensesPage";
import LoansPage from "../pages/LoansPage";
import AnalyticsPage from "../pages/AnalyticsPage";
import AiAssistantPage from "../pages/AiAssistantPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/expenses" element={<ExpensesPage />} />
      <Route path="/loans" element={<LoansPage />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
      <Route path="/assistant" element={<AiAssistantPage />} />
    </Routes>
  );
}