// App.jsx - The top of our React app: decides what to show.

import { useEffect, useState } from "react";
import { api, clearToken, getToken } from "./api";
import AuthPage from "./pages/AuthPage";
import "./App.css";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(getToken()));

  // On page load: if a token is saved, ask the backend "who am I?"
  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => clearToken()) // expired or invalid token -> forget it
      .finally(() => setChecking(false));
  }, []);

  function logout() {
    clearToken();
    setUser(null);
  }

  if (checking) return <p className="center muted">Loading...</p>;
  if (!user) return <AuthPage onLoggedIn={setUser} />;

  return (
    <div className="app">
      <header className="topbar">
        <strong>🎟️ Seat Booking</strong>
        <span className="spacer" />
        <span>Hi, {user.full_name}</span>
        <button onClick={logout}>Log out</button>
      </header>
      <main className="content">
        <div className="card">
          <h2>You're logged in ✅</h2>
          <p className="muted">Shows and the seat map come in the next step.</p>
        </div>
      </main>
    </div>
  );
}