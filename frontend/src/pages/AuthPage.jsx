// AuthPage.jsx - Log in, or create an account (then log in automatically).

import { useState } from "react";
import { api, saveToken } from "../api";

export default function AuthPage({ onLoggedIn }) {
  const [mode, setMode] = useState("login"); // "login" or "signup"
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault(); // stop the browser from reloading the page
    setError("");
    setBusy(true);
    try {
      if (mode === "signup") {
        await api.signup(email, fullName, password);
      }
      const { access_token } = await api.login(email, password);
      saveToken(access_token);
      const user = await api.me();
      onLoggedIn(user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const isSignup = mode === "signup";

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <h1>🎟️ Seat Booking</h1>
        <p className="muted">{isSignup ? "Create your account" : "Log in to book seats"}</p>

        {isSignup && (
          <label>
            Full name
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </label>
        )}

        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>

        <label>
          Password {isSignup && <span className="muted">(at least 8 characters)</span>}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </label>

        {error && <p className="error">{error}</p>}

        <button className="primary" type="submit" disabled={busy}>
          {busy ? "Please wait..." : isSignup ? "Sign up" : "Log in"}
        </button>

        <button
          type="button"
          className="link"
          onClick={() => {
            setMode(isSignup ? "login" : "signup");
            setError("");
          }}
        >
          {isSignup ? "Already have an account? Log in" : "New here? Create an account"}
        </button>
      </form>
    </div>
  );
}