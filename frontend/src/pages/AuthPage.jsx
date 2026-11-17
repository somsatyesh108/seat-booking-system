// AuthPage.jsx - The /login and /signup pages. After signing in, the user goes back to
// the page they were trying to open (for example, a seat map).

import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/authContext";
import Logo from "../components/Logo";

export default function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const { user, login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const goTo = location.state?.from || "/";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Already signed in? No need to see this page.
  if (user) return <Navigate to={goTo} replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isSignup) {
        await signup(fullName, email, password);
      } else {
        await login(email, password);
      }
      navigate(goTo, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-hero">
        <Link to="/" className="logo" aria-label="Bookify home">
          <Logo />
        </Link>

        <div>
          <h1>{isSignup ? "Your next night out starts here." : "Good to see you again."}</h1>
          <p>
            Movies, buses and events across Bengaluru. Pick your seats and we hold them for five
            minutes while you pay.
          </p>
        </div>

        <ul className="auth-facts">
          <li>Seats held for 5 minutes, just for you</li>
          <li>Two people can never book the same seat</li>
          <li>All your tickets in one place</li>
        </ul>
      </section>

      <section className="auth-form-wrap">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h2>{isSignup ? "Create your account" : "Sign in"}</h2>

          {location.state?.from && (
            <p className="notice notice-info">Sign in to continue with your booking.</p>
          )}

          {isSignup && (
            <label className="field">
              Full name
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} autoComplete="name" required />
            </label>
          )}

          <label className="field">
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          </label>

          <label className="field">
            Password
            {isSignup && <span className="field-hint">At least 8 characters</span>}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isSignup ? "new-password" : "current-password"}
              minLength={8}
              required
            />
          </label>

          {error && <p className="notice notice-error" role="alert">{error}</p>}

          <button className="btn btn-primary btn-large btn-block" type="submit" disabled={busy}>
            {busy ? "Please wait..." : isSignup ? "Create account" : "Sign in"}
          </button>

          <p className="auth-switch">
            {isSignup ? "Already have an account? " : "New to Bookify? "}
            <Link to={isSignup ? "/login" : "/signup"} state={location.state}>
              {isSignup ? "Sign in" : "Create an account"}
            </Link>
          </p>
        </form>
      </section>
    </div>
  );
}