// App.jsx - The top of our React app: decides which screen to show.

import { useEffect, useState } from "react";
import { api, clearToken, getToken } from "./api";
import AuthPage from "./pages/AuthPage";
import MyBookingsPage from "./pages/MyBookingsPage";
import SeatMapPage from "./pages/SeatMapPage";
import ShowsPage from "./pages/ShowsPage";
import "./App.css";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(getToken()));
  const [tab, setTab] = useState("shows"); // "shows" or "bookings"
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
    setTab("shows");
  }

  function openTab(name) {
    setTab(name);
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
        <nav className="tabs">
          <button className={tab === "shows" ? "active" : ""} onClick={() => openTab("shows")}>
            🎬 Shows
          </button>
          <button className={tab === "bookings" ? "active" : ""} onClick={() => openTab("bookings")}>
            🎟️ My bookings
          </button>
        </nav>

        {tab === "bookings" ? (
          <MyBookingsPage onBrowseShows={() => openTab("shows")} />
        ) : selectedShow ? (
          <SeatMapPage
            key={selectedShow.id}
            show={selectedShow}
            onBack={() => setSelectedShow(null)}
          />
        ) : (
          <ShowsPage onSelectShow={setSelectedShow} />
        )}
      </main>
    </div>
  );
}