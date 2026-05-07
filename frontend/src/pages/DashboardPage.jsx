import { Link, useNavigate } from "react-router-dom";
import "../styles/dashboard.css";

export default function DashboardPage() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  const features = [
    {
      title: "Expenses",
      icon: "💸",
      description:
        "Track your income and outcomes, manage categories, and keep your financial records organized.",
      path: "/expenses",
      action: "Open Expenses",
    },
    {
      title: "Loans",
      icon: "🤝",
      description:
        "Create loans, update repayment status, and manage lending and borrowing records.",
      path: "/loans",
      action: "Open Loans",
    },
    {
      title: "Analytics",
      icon: "📊",
      description:
        "View summaries, financial trends, and performance indicators for your money activity.",
      path: "/analytics",
      action: "Open Analytics",
    },
  ];

  return (
    <div className="dashboard-page">
      <div className="dashboard-shell">

        {/* Top bar */}
        <div className="dashboard-topbar">
          <div>
            <h1 className="dashboard-title">AMMA Dashboard</h1>

            <p className="dashboard-subtitle">
              AI Money Management Assistant
            </p>
          </div>

          <button
            className="btn btn-danger"
            onClick={handleLogout}
          >
            <span className="btn-icon">🚪</span>

            <span className="btn-label">
              Logout
            </span>
          </button>
        </div>


        {/* Welcome block */}
        <div className="dashboard-hero">
          <div className="dashboard-hero-card">
            <h2>Welcome back</h2>

            <p>
              Manage your expenses, loans, and financial activity from one
              place with a cleaner and more organized workflow.
            </p>
          </div>
        </div>


        {/* Feature cards */}
        <div className="dashboard-grid">

          {features.map((item) => (

            <div
              key={item.title}
              className="dashboard-feature-card"
            >

              <h3>{item.title}</h3>

              <p>{item.description}</p>

              <Link
                to={item.path}
                className="btn btn-primary"
              >

                <span className="btn-icon">
                  {item.icon}
                </span>

                <span className="btn-label">
                  {item.action}
                </span>

              </Link>

            </div>

          ))}

        </div>

      </div>
    </div>
  );
}