import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SiteHeader from "../components/SiteHeader.jsx";
import { login, setToken } from "../api/client.js";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle");
  const navigate = useNavigate();

  function handleSubmit(event) {
    event.preventDefault();
    setStatus("submitting");
    setError("");

    login({ username, password })
      .then((data) => {
        setToken(data.access_token);
        navigate("/admin", { replace: true });
      })
      .catch((err) => {
        setStatus("idle");
        setError(err.message);
      });
  }

  return (
    <div className="site-shell">
      <SiteHeader eyebrow="Admin" />
      <main className="site-main">
        <div className="panel panel--raised">
          <h1>Admin login</h1>
          <form onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && <p className="error-text">{error}</p>}

            <button type="submit" className="primary-button" disabled={status === "submitting"}>
              {status === "submitting" ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
