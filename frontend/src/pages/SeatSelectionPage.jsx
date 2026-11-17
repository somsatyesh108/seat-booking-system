// SeatSelectionPage.jsx - Pick seats for one showtime. Each seat you tap is held for you in
// Redis for 5 minutes. A sticky bar shows your seats, the countdown and the total.

import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { loadHolds, saveHolds } from "../holdStore";
import {
  expiresAtFromNow,
  formatCountdown,
  formatDay,
  formatTime,
  priceLabel,
  rupees,
  slugify,
} from "../utils";
import "../styles/seats.css";

const REFRESH_EVERY_MS = 5000;
const MAX_SEATS = 10;
const FRONT_LABEL = { movie: "Screen this way", bus: "Front of the bus", event: "Stage" };

// Turn the flat seat list into price tiers: [{ price, rows: [{ label, seats }] }]
function buildTiers(seats) {
  const rows = [];
  for (const seat of seats) {
    const last = rows.at(-1);
    if (last && last.label === seat.row_label) last.seats.push(seat);
    else rows.push({ label: seat.row_label, seats: [seat] });
  }
  const tiers = [];
  for (const row of rows) {
    const price = row.seats[0].price_paise;
    const last = tiers.at(-1);
    if (last && last.price === price) last.rows.push(row);
    else tiers.push({ price, rows: [row] });
  }
  return tiers;
}

function rowsText(rows) {
  if (rows.length === 1) return `Row ${rows[0].label}`;
  return `Rows ${rows[0].label} to ${rows.at(-1).label}`;
}

export default function SeatSelectionPage() {
  const { showId } = useParams();
  const id = Number(showId);
  const navigate = useNavigate();

  const [seatMap, setSeatMap] = useState(null);
  const [myHolds, setMyHolds] = useState(() => loadHolds(id)); // { seatId: expiresAt }
  const [now, setNow] = useState(() => Date.now());
  const [error, setError] = useState("");
  const [busySeatId, setBusySeatId] = useState(null);

  // Keep a "pocket" copy for the timer, and remember holds across a page refresh.
  const holdsRef = useRef(myHolds);
  useEffect(() => {
    holdsRef.current = myHolds;
    saveHolds(id, myHolds);
  }, [id, myHolds]);

  const loadSeats = useCallback(() => {
    return api
      .seatMap(id)
      .then((map) => {
        setSeatMap(map);
        // Double-check with the server: drop any "mine" seat that is no longer held.
        const statusById = new Map(map.seats.map((seat) => [seat.id, seat.status]));
        setMyHolds((holds) => {
          const stillHeld = Object.entries(holds).filter(
            ([seatId]) => statusById.get(Number(seatId)) === "held"
          );
          return stillHeld.length === Object.keys(holds).length ? holds : Object.fromEntries(stillHeld);
        });
      })
      .catch((err) => setError(err.message));
  }, [id]);

  // Load now, then refresh every 5 seconds to see other people's holds and bookings.
  useEffect(() => {
    loadSeats();
    const timer = setInterval(loadSeats, REFRESH_EVERY_MS);
    return () => clearInterval(timer);
  }, [loadSeats]);

  // Every second: move the countdown and drop my holds that have run out.
  useEffect(() => {
    const timer = setInterval(() => {
      const current = Date.now();
      setNow(current);
      const holds = holdsRef.current;
      const expiredIds = Object.keys(holds).filter((seatId) => holds[seatId] <= current);
      if (expiredIds.length > 0) {
        setMyHolds((latest) => {
          const next = { ...latest };
          expiredIds.forEach((seatId) => delete next[seatId]);
          return next;
        });
        setError("Your 5-minute hold ran out, so those seats were released. Please pick again.");
        loadSeats();
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [loadSeats]);

  async function handleSeatClick(seat) {
    const isMine = seat.id in myHolds;
    if (!isMine && seat.status !== "available") return;
    if (!isMine && Object.keys(myHolds).length >= MAX_SEATS) {
      setError(`You can book up to ${MAX_SEATS} seats at a time.`);
      return;
    }

    setError("");
    setBusySeatId(seat.id);
    try {
      if (isMine) {
        await api.releaseSeat(id, seat.id);
        setMyHolds((holds) => {
          const next = { ...holds };
          delete next[seat.id];
          return next;
        });
      } else {
        const hold = await api.holdSeat(id, seat.id);
        const expiresAt = expiresAtFromNow(hold.expires_in_seconds);
        setMyHolds((holds) => ({ ...holds, [seat.id]: expiresAt }));
      }
    } catch (err) {
      setError(err.message); // e.g. "Seat A1 is being held by someone else..."
    } finally {
      setBusySeatId(null);
      loadSeats();
    }
  }

  if (!seatMap) {
    return error ? <p className="page-empty">{error}</p> : <p className="page-loading">Loading seats...</p>;
  }

  const { show, seats } = seatMap;
  const tiers = buildTiers(seats);
  const myIds = Object.keys(myHolds).map(Number);
  const mySeats = seats.filter((seat) => myIds.includes(seat.id));
  const totalPaise = mySeats.reduce((sum, seat) => sum + seat.price_paise, 0);
  const soonestExpiry = myIds.length > 0 ? Math.min(...Object.values(myHolds)) : null;

  const stateOf = (seat) => (seat.id in myHolds ? "mine" : seat.status);
  const STATE_TEXT = { available: "available", mine: "your seat", held: "held by someone", booked: "sold" };

  return (
    <>
      <div className="seats-top">
        <div className="container seats-top-inner">
          <Link to={`/title/${slugify(show.title)}`} className="back-link">
            ‹ {show.title}
          </Link>
          <p>
            {show.venue}, {formatDay(show.starts_at)}, {formatTime(show.starts_at)}
          </p>
        </div>
      </div>

      <div className="container seats-page">
        <ul className="seat-legend">
          <li><span className="swatch is-available" /> Available</li>
          <li><span className="swatch is-mine" /> Your seats</li>
          <li><span className="swatch is-held" /> Held by someone</li>
          <li><span className="swatch is-booked" /> Sold</li>
        </ul>

        <div className="front">{FRONT_LABEL[show.category] || "Front"}</div>

        {error && <p className="notice notice-error seats-notice" role="alert">{error}</p>}

        <div className="seat-hall">
          {tiers.map((tier) => (
            <div className="tier" key={`${tier.price}-${tier.rows[0].label}`}>
              <div className="tier-label">
                <strong>{priceLabel(tier.price)}</strong>
                {rowsText(tier.rows)}
              </div>
              <div className="tier-rows">
                {tier.rows.map((row) => {
                  const aisleAfter = Math.floor(row.seats.length / 2);
                  return (
                    <div className="seat-line" key={row.label}>
                      <span className="row-name">{row.label}</span>
                      {row.seats.map((seat, index) => {
                        const state = stateOf(seat);
                        const clickable = state === "available" || state === "mine";
                        return (
                          <button
                            key={seat.id}
                            className={`seat-btn is-${state}${index + 1 === aisleAfter ? " aisle" : ""}`}
                            disabled={!clickable || busySeatId !== null}
                            aria-pressed={state === "mine"}
                            aria-label={`${seat.label}, ${priceLabel(seat.price_paise)}, ${STATE_TEXT[state]}`}
                            title={`${seat.label}, ${priceLabel(seat.price_paise)}`}
                            onClick={() => handleSeatClick(seat)}
                          >
                            {seat.seat_number}
                          </button>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {myIds.length > 0 && (
        <div className="checkout-bar">
          <div className="container checkout-bar-inner">
            <div className="bar-seats">
              <strong>
                {myIds.length} seat{myIds.length > 1 ? "s" : ""}
              </strong>
              <span>{mySeats.map((seat) => seat.label).join(", ")}</span>
            </div>
            <span className="hold-timer">Held for {formatCountdown(soonestExpiry - now)}</span>
            <span className="bar-spacer" />
            <span className="bar-total">{rupees(totalPaise)}</span>
            <button className="btn btn-primary btn-large" onClick={() => navigate(`/checkout/${id}`)}>
              Continue
            </button>
          </div>
        </div>
      )}
    </>
  );
}