// ConfirmationPage.jsx - "You're all set": an animated tick and a ticket stub for the new booking.
// The booking details arrive from the checkout page (router state). If someone opens this
// page directly, they are sent to My tickets instead.

import { Link, Navigate, useLocation } from "react-router-dom";
import { formatDay, formatTime, rupees } from "../utils";
import "../styles/checkout.css";

const KIND = { movie: "Movie ticket", bus: "Bus ticket", event: "Event ticket" };

export default function ConfirmationPage() {
  const { state } = useLocation();
  if (!state?.confirmation) return <Navigate to="/tickets" replace />;

  const { confirmation, show, paidWith } = state;
  const seatLabels = confirmation.bookings
    .map((booking) => booking.seat_label)
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  const reference = `BKF-${String(confirmation.bookings[0].id).padStart(6, "0")}`;
  const total = confirmation.total_paise;

  return (
    <div className="container confirm">
      <div className="confirm-check" aria-hidden="true">
        <svg viewBox="0 0 52 52">
          <circle cx="26" cy="26" r="26" />
          <path d="M15 27l7 7 15-15" />
        </svg>
      </div>

      <h1>You're all set.</h1>
      <p className="confirm-sub">Your booking is confirmed and saved in My tickets.</p>

      <article className="ticket" aria-label="Your ticket">
        <div className="ticket-main">
          <span className="ticket-kind">{KIND[show.category]}</span>
          <h2>{show.title}</h2>
          <dl className="ticket-details">
            <div>
              <dt>Date</dt>
              <dd>{formatDay(show.starts_at)}</dd>
            </div>
            <div>
              <dt>Time</dt>
              <dd>{formatTime(show.starts_at)}</dd>
            </div>
            <div>
              <dt>Venue</dt>
              <dd>{show.venue}</dd>
            </div>
            <div>
              <dt>{seatLabels.length > 1 ? "Seats" : "Seat"}</dt>
              <dd>{seatLabels.join(", ")}</dd>
            </div>
          </dl>
        </div>

        <div className="ticket-stub">
          <div className="barcode" aria-hidden="true" />
          <dl>
            <div>
              <dt>Booking reference</dt>
              <dd>{reference}</dd>
            </div>
            <div>
              <dt>Paid</dt>
              <dd>
                {total === 0 ? "Free" : rupees(total)}
                {paidWith ? ` with ${paidWith}` : ""}
              </dd>
            </div>
          </dl>
        </div>
      </article>

      <div className="confirm-actions">
        <Link className="btn btn-primary btn-large" to="/tickets">View my tickets</Link>
        <Link className="btn btn-secondary btn-large" to="/">Book something else</Link>
      </div>
    </div>
  );
}