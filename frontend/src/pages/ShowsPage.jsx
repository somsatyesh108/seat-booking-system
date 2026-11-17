// ShowsPage.jsx - A list of shows (movies, bus trips, events) to choose from.

import { useEffect, useState } from "react";
import { api } from "../api";
import { formatDate } from "../utils";

const ICONS = { movie: "🎬", bus: "🚌", event: "🎤" };

export default function ShowsPage({ onSelectShow }) {
  const [shows, setShows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Load the shows once, when this page first appears.
  useEffect(() => {
    api
      .listShows()
      .then(setShows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="muted">Loading shows...</p>;
  if (error) return <p className="error">{error}</p>;
  if (shows.length === 0) return <p className="muted">No shows yet.</p>;

  return (
    <>
      <h2>Choose a show</h2>
      <div className="show-list">
        {shows.map((show) => (
          <button key={show.id} className="card show-card" onClick={() => onSelectShow(show)}>
            <span className="badge">
              {ICONS[show.category] || "🎟️"} {show.category}
            </span>
            <strong>{show.title}</strong>
            <span className="muted">{show.venue}</span>
            <span className="muted">{formatDate(show.starts_at)}</span>
          </button>
        ))}
      </div>
    </>
  );
}