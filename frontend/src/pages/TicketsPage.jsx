// TicketsPage.jsx - My tickets: bookings grouped per showtime, split into Upcoming and Past.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { formatTime, rupees, slugify } from "../utils";
import "../styles/tickets.css";

const KIND = { movie: "Movie ticket", bus: "Bus ticket", event: "Event ticket" };

// "2026-12-05T13:30:00Z" -> { weekday: "Sat", day: "5", month: "Dec" } in Indian time
function dateParts(isoText) {
  const date = new Date(isoText);
  const part = (options) =>
    date.toLocaleDateString("en-IN", { ...options, timeZone: "Asia/Kolkata" });
  return {
    weekday: part({ weekday: "short" }),
    day: part({ day: "numeric" }),
    month: part({ month: "short" }),
  };
}

const bySeatOrder = (a, b) => a.localeCompare(b, undefined, { numeric: true });

export default function TicketsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("upcoming");
  const [now] = useState(() => Date.now());

  // My bookings + all shows (for each booking's date, venue and category).
  useEffect(() => {
    Promise.all([api.myBookings(), api.listShows()])
      .then(([bookings, shows]) => setData({ bookings, shows }))
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="page-empty">{error}</p>;
  if (!data) return <p className="page-loading">Loading your tickets...</p>;

  // Group seats into one "order" per showtime.
  const showsById = new Map(data.shows.map((show) => [show.id, show]));
  const orders = new Map();
  for (const booking of data.bookings) {
    const show = showsById.get(booking.show_id);
    if (!show) continue;
    if (!orders.has(show.id)) {
      orders.set(show.id, { show, seats: [], totalPaise: 0, firstBookingId: booking.id });
    }
    const order = orders.get(show.id);
    order.seats.push(booking.seat_label);
    order.totalPaise += booking.amount_paise;
    order.firstBookingId = Math.min(order.firstBookingId, booking.id);
  }

  const all = [...orders.values()].sort((a, b) => a.show.starts_at.localeCompare(b.show.starts_at));
  const upcoming = all.filter((order) => new Date(order.show.starts_at).getTime() >= now);
  const past = all.filter((order) => new Date(order.show.starts_at).getTime() < now).reverse();
  const visible = tab === "upcoming" ? upcoming : past;

  return (
    <div className="container tickets">
      <h1>My tickets</h1>

      <div className="ticket-tabs" role="group" aria-label="Which tickets to show">
        <button aria-pressed={tab === "upcoming"} onClick={() => setTab("upcoming")}>
          Upcoming ({upcoming.length})
        </button>
        <button aria-pressed={tab === "past"} onClick={() => setTab("past")}>
          Past ({past.length})
        </button>
      </div>

      {visible.length === 0 ? (
        <div className="tickets-empty">
          <h2>{tab === "upcoming" ? "No upcoming tickets" : "No past tickets yet"}</h2>
          <p>
            {tab === "upcoming"
              ? "When you book a movie, a bus or an event, your ticket will appear here."
              : "Tickets for shows that have already happened will move here."}
          </p>
          <Link className="btn btn-primary" to="/">Find something to book</Link>
        </div>
      ) : (
        <ul className="ticket-list">
          {visible.map((order) => {
            const parts = dateParts(order.show.starts_at);
            const seats = [...order.seats].sort(bySeatOrder);
            return (
              <li className="ticket-row" key={order.show.id}>
                <div className="ticket-date" aria-hidden="true">
                  <span>{parts.weekday}</span>
                  <strong>{parts.day}</strong>
                  <span>{parts.month}</span>
                </div>

                <div className="ticket-info">
                  <span className="ticket-row-kind">{KIND[order.show.category]}</span>
                  <Link className="ticket-title" to={`/title/${slugify(order.show.title)}`}>
                    {order.show.title}
                  </Link>
                  <p>{order.show.venue}</p>
                  <p>
                    {parts.weekday}, {parts.day} {parts.month}, {formatTime(order.show.starts_at)}
                  </p>
                </div>

                <div className="ticket-side">
                  <dl>
                    <div>
                      <dt>{seats.length > 1 ? "Seats" : "Seat"}</dt>
                      <dd>{seats.join(", ")}</dd>
                    </div>
                    <div>
                      <dt>Reference</dt>
                      <dd>BKF-{String(order.firstBookingId).padStart(6, "0")}</dd>
                    </div>
                    <div>
                      <dt>Paid</dt>
                      <dd>{order.totalPaise === 0 ? "Free" : rupees(order.totalPaise)}</dd>
                    </div>
                  </dl>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}