// MyBookingsPage.jsx - All of the logged-in user's bookings, grouped by show.

import { useEffect, useState } from "react";
import { api } from "../api";
import { formatDate, rupees } from "../utils";

export default function MyBookingsPage({ onBrowseShows }) {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .myBookings()
      .then(setBookings)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="muted">Loading your bookings...</p>;
  if (error) return <p className="error">{error}</p>;
  if (bookings.length === 0) {
    return (
      <div className="card">
        <h2>No bookings yet</h2>
        <p className="muted">Pick a show and grab some seats!</p>
        <button className="primary" onClick={onBrowseShows}>Browse shows</button>
      </div>
    );
  }

  // Group bookings by show: { showId: { title, seats: [...], total } }
  const byShow = {};
  bookings.forEach((booking) => {
    const group = (byShow[booking.show_id] ??= {
      title: booking.show_title,
      seats: [],
      totalPaise: 0,
      lastBookedAt: booking.created_at,
    });
    group.seats.push(booking.seat_label);
    group.totalPaise += booking.amount_paise;
  });

  const grandTotal = bookings.reduce((sum, booking) => sum + booking.amount_paise, 0);

  return (
    <>
      <h2>My bookings</h2>
      {Object.entries(byShow).map(([showId, group]) => (
        <div className="card" key={showId}>
          <strong>{group.title}</strong>
          <p style={{ margin: "6px 0" }}>
            Seats: <strong>{group.seats.sort().join(", ")}</strong>
          </p>
          <p className="muted" style={{ margin: 0 }}>
            {group.seats.length} seat{group.seats.length > 1 ? "s" : ""} · {rupees(group.totalPaise)} ·
            booked {formatDate(group.lastBookedAt)}
          </p>
        </div>
      ))}
      <p className="muted">
        Total: <strong>{bookings.length} seats</strong> · <strong>{rupees(grandTotal)}</strong>
      </p>
    </>
  );
}