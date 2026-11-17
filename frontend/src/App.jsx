// App.jsx - The top of our React app: decides which screen to show.

import { useEffect, useState } from "react";
import { api, clearToken, getToken } from "./api";
import AuthPage from "./pages/AuthPage";
import ShowsPage from "./pages/ShowsPage";
import "./App.css";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(getToken()));
  const [selectedShow, setSelectedShow] = useState(null);

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
    setSelectedShow(null);
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
        {selectedShow ? (
          <div className="card">
            <button onClick={() => setSelectedShow(null)}>← Back to shows</button>
            <h2>{selectedShow.title}</h2>
            <p className="muted">The clickable seat map comes in the next step.</p>
          </div>
        ) : (
          <ShowsPage onSelectShow={setSelectedShow} />
        )}
      </main>
    </div>
  );
}