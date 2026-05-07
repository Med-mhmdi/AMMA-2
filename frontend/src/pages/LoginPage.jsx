import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import authApi from "../api/authApi";
import "../styles/auth.css";

export default function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      alert("Please enter email and password");
      return;
    }

    try {
      setLoading(true);

      const data = await authApi.login({
        email,
        password,
      });

      localStorage.setItem("token", data.access_token);

      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      alert(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  // Allow pressing Enter to submit login
  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleLogin();
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Login</h1>

        <label className="auth-label">Email</label>
        <input
          className="auth-input"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onKeyDown={handleKeyPress}
        />

        <label className="auth-label">Password</label>
        <input
          className="auth-input"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={handleKeyPress}
        />

        <button
          className="auth-button"
          onClick={handleLogin}
          disabled={loading}
        >
          {loading ? "Logging in..." : "Login"}
        </button>

        <p className="auth-footer-text">
          Don&apos;t have an account?{" "}
          <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}