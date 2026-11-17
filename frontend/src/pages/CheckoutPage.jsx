// CheckoutPage.jsx - Review the seats you are holding, pick a (demo) payment method, and confirm.
// Clicking Pay calls POST /bookings: the backend's 3 safety layers decide if the booking succeeds.

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth/authContext";
import Poster from "../components/Poster";
import { clearHolds, loadHolds } from "../holdStore";
import { formatCountdown, formatDay, formatDuration, formatTime, priceLabel, rupees } from "../utils";
import "../styles/checkout.css";

const PAYMENT_METHODS = [
  { id: "UPI", note: "Google Pay, PhonePe, Paytm and others" },
  { id: "Card", note: "Credit or debit card" },
  { id: "Net banking", note: "All major banks" },
];

export default function CheckoutPage() {
  const { showId } = useParams();
  const id = Number(showId);
  const navigate = useNavigate();
  const { user } = useAuth();

  const [seatMap, setSeatMap] = useState(null);
  const [holds] = useState(() => loadHolds(id)); // { seatId: expiresAt }
  const [now, setNow] = useState(() => Date.now());
  const [method, setMethod] = useState("UPI");
  const [error, setError] = useState("");
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    api.seatMap(id).then(setSeatMap).catch((err) => setError(err.message));
  }, [id]);

  // Tick every second so the "held for" countdown moves.
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!seatMap) {
    return error ? <p className="page-empty">{error}</p> : <p className="page-loading">Loading your booking...</p>;
  }

  const { show, seats } = seatMap;
  // Only seats that we remember holding AND the server still shows as held.
  const mySeats = seats.filter((seat) => seat.id in holds && seat.status === "held");
  const expiresAt = mySeats.length > 0 ? Math.min(...mySeats.map((seat) => holds[seat.id])) : 0;
  const timeLeft = expiresAt - now;
  const holdEnded = mySeats.length === 0 || timeLeft <= 0;
  const totalPaise = mySeats.reduce((sum, seat) => sum + seat.price_paise, 0);
  const facts = [show.genre, show.language, formatDuration(show.duration_minutes)].filter(Boolean);

  async function handlePay() {
    setError("");
    setPaying(true);
    try {
      const confirmation = await api.book(id, mySeats.map((seat) => seat.id));
      clearHolds(id);
      navigate("/booking/confirmed", {
        replace: true,
        state: { confirmation, show, paidWith: totalPaise === 0 ? "" : method },
      });
    } catch (err) {
      setError(err.message); // e.g. "Hold these seats before booking..." if the hold just ran out
      setPaying(false);
    }
  }

  return (
    <div className="container checkout">
      <Link to={`/shows/${id}/seats`} className="checkout-back">‹ Change seats</Link>
      <h1>Review and pay</h1>

      {holdEnded ? (
        <div className="checkout-card">
          <h2>Your seats are no longer held</h2>
          <p className="muted-text">
            Seat holds last 5 minutes. Pick your seats again and you'll be back here in a moment.
          </p>
          <p style={{ marginTop: 16 }}>
            <Link className="btn btn-primary" to={`/shows/${id}/seats`}>Choose seats again</Link>
          </p>
        </div>
      ) : (
        <div className="checkout-layout">
          <div className="checkout-main">
            <section className="checkout-card show-summary">
              <Poster item={show} />
              <div>
                <h2>{show.title}</h2>
                <p>{show.venue}</p>
                <p>
                  {formatDay(show.starts_at)}, {formatTime(show.starts_at)}
                </p>
                {facts.length > 0 && <p className="muted-text">{facts.join(", ")}</p>}
              </div>
            </section>

            <section className="checkout-card">
              <h2>Your seats</h2>
              <ul className="seat-lines">
                {mySeats.map((seat) => (
                  <li key={seat.id}>
                    <span>Seat {seat.label}</span>
                    <span>{priceLabel(seat.price_paise)}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="checkout-card">
              <h2>Contact details</h2>
              <p>{user.full_name}</p>
              <p className="muted-text">{user.email}. Your tickets will appear in My tickets.</p>
            </section>

            {totalPaise > 0 && (
              <section className="checkout-card">
                <h2>Payment method</h2>
                <div className="pay-options" role="radiogroup" aria-label="Payment method">
                  {PAYMENT_METHODS.map((option) => (
                    <label
                      key={option.id}
                      className={`pay-option${method === option.id ? " selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name="payment"
                        value={option.id}
                        checked={method === option.id}
                        onChange={() => setMethod(option.id)}
                      />
                      <span>
                        <strong>{option.id}</strong>
                        <small>{option.note}</small>
                      </span>
                    </label>
                  ))}
                </div>
                <p className="notice notice-info">
                  This is a demo. No real payment is taken and no card or UPI details are collected.
                </p>
              </section>
            )}
          </div>

          <aside className="checkout-summary" aria-label="Order summary">
            <div className="hold-banner">Seats held for {formatCountdown(timeLeft)}</div>
            <h2>Order summary</h2>
            <dl className="summary-lines">
              <div>
                <dt>Tickets ({mySeats.length})</dt>
                <dd>{rupees(totalPaise)}</dd>
              </div>
              <div>
                <dt>Booking fee</dt>
                <dd>Free</dd>
              </div>
              <div className="total">
                <dt>Total</dt>
                <dd>{totalPaise === 0 ? "Free" : rupees(totalPaise)}</dd>
              </div>
            </dl>

            {error && <p className="notice notice-error" role="alert">{error}</p>}

            <button className="btn btn-primary btn-large btn-block" disabled={paying} onClick={handlePay}>
              {paying ? "Confirming..." : totalPaise === 0 ? "Confirm booking" : `Pay ${rupees(totalPaise)}`}
            </button>
            <p className="fine-print">Bookify is a portfolio project. Bookings are real in the app; payments are not.</p>
          </aside>
        </div>
      )}
    </div>
  );
}