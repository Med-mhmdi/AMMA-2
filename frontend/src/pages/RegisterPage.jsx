import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import authApi from "../api/authApi";
import "../styles/auth.css";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    phone_number: "",
    password: "",
    first_name: "",
    family_name: "",
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleRegister = async () => {
    if (
      !form.email ||
      !form.phone_number ||
      !form.password ||
      !form.first_name ||
      !form.family_name
    ) {
      alert("Please fill all required fields");
      return;
    }

    try {
      setLoading(true);

      await authApi.register({
        email: form.email,
        phone_number: form.phone_number,
        password: form.password,
        first_name: form.first_name,
        family_name: form.family_name,
      });

      alert("Registration successful");

      navigate("/");
    } catch (err) {
      console.error(err);
      alert(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  // Enable Enter key submission
  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleRegister();
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Register</h1>

        <label className="auth-label">First Name</label>
        <input
          className="auth-input"
          name="first_name"
          value={form.first_name}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          placeholder="Enter your first name"
        />

        <label className="auth-label">Family Name</label>
        <input
          className="auth-input"
          name="family_name"
          value={form.family_name}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          placeholder="Enter your family name"
        />

        <label className="auth-label">Email</label>
        <input
          className="auth-input"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          placeholder="Enter your email"
        />

        <label className="auth-label">Phone Number</label>
        <input
          className="auth-input"
          name="phone_number"
          value={form.phone_number}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          placeholder="Enter your phone number"
        />

        <label className="auth-label">Password</label>
        <input
          className="auth-input"
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          placeholder="Enter your password"
        />

        <button
          className="auth-button"
          onClick={handleRegister}
          disabled={loading}
        >
          {loading ? "Registering..." : "Register"}
        </button>

        <p className="auth-footer-text">
          Already have an account? <Link to="/">Login</Link>
        </p>
      </div>
    </div>
  );
}