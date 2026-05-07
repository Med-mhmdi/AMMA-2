import { Link } from "react-router-dom";

export default function PageHeader({ title }) {
  return (
    <div className="page-header">
      <Link to="/dashboard" className="page-header-action btn btn-header">
        <span className="btn-icon">🏠</span>
        <span className="btn-label">Dashboard</span>
      </Link>

      <h1 className="page-title">{title}</h1>
    </div>
  );
}