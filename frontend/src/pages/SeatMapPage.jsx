// SeatMapPage.jsx - Live seat map: hold seats (5-minute timer), release them, and book them.

import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { formatDate } from "./ShowsPage";

const REFRESH_EVERY_MS = 5000; // re-load the map every 5 s to see other people's holds
const FRONT_LABEL = { movie: "SCREEN", bus: "FRONT", event: "STAGE" };

// 25000 paise -> "₹250"
export function rupees(paise) {
  return `₹${(paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

// 299000 ms -> "4:59"
function formatCountdown(ms) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export default function SeatMapPage({ show, onBack }) {
  const [seatMap, setSeatMap] = useState(null);
  const [myHolds, setMyHolds] = useState({}); // { seatId: expiresAt (ms) }
  const [now, setNow] = useState(Date.now());
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const loadSeats = useCallback(() => {
    return api
      .seatMap(show.id)
      .then(setSeatMap)
      .catch((err) => setError(err.message));
  }, [show.id]);

  // Load the map now, then refresh it every 5 seconds.
  useEffect(() => {
    loadSeats();
    const timer = setInterval(loadSeats, REFRESH_EVERY_MS);
    return () => clearInterval(timer); // stop refreshing when we leave this page
  }, [loadSeats]);

  // Tick once a second, so the countdown moves.
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // When one of my holds runs out, forget it and tell the user.
  useEffect(() => {
    const expiredIds = Object.keys(myHolds).filter((seatId) => myHolds[seatId] <= now);
    if (expiredIds.length === 0) return;
    setMyHolds((holds) => {
      const next = { ...holds };
      expiredIds.forEach((seatId) => delete next[seatId]);
      return next;
    });
    setMessage("");
    setError("Your 5-minute hold expired, so those seats were released. Please choose again.");
    loadSeats();
  }, [now, myHolds, loadSeats]);

  async function handleSeatClick(seat) {
    const isMine = seat.id in myHolds;
    if (!isMine && seat.status !== "available") return;

    setError("");
    setMessage("");
    setBusy(true);
    try {
      if (isMine) {
        await api.releaseSeat(show.id, seat.id);
        setMyHolds((holds) => {
          const next = { ...holds };
          delete next[seat.id];
          return next;
        });
      } else {
        const hold = await api.holdSeat(show.id, seat.id);
        const expiresAt = Date.now() + hold.expires_in_seconds * 1000;
        setMyHolds((holds) => ({ ...holds, [seat.id]: expiresAt }));
      }
    } catch (err) {
      setError(err.message); // e.g. "Seat A1 is being held by someone else..."
    } finally {
      setBusy(false);
      loadSeats();
    }
  }

  async function handleBook() {
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const seatIds = Object.keys(myHolds).map(Number);
      const result = await api.book(show.id, seatIds);
      setMyHolds({});
      const labels = result.bookings.map((booking) => booking.seat_label).join(", ");
      setMessage(`Booked ${labels} for ${rupees(result.total_paise)} 🎉`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      loadSeats();
    }
  }

  if (!seatMap) {
    return error ? <p className="error">{error}</p> : <p className="muted">Loading seats...</p>;
  }

  // Group seats into rows: { A: [A1, A2, ...], B: [...] }
  const rows = {};
  seatMap.seats.forEach((seat) => {
    (rows[seat.row_label] ??= []).push(seat);
  });

  const myHeldIds = Object.keys(myHolds).map(Number);
  const myHeldSeats = seatMap.seats.filter((seat) => myHeldIds.includes(seat.id));
  const totalPaise = myHeldSeats.reduce((sum, seat) => sum + seat.price_paise, 0);
  const soonestExpiry = myHeldIds.length > 0 ? Math.min(...Object.values(myHolds)) : null;

  const colourOf = (seat) => (seat.id in myHolds ? "mine" : seat.status);

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <button onClick={onBack}>← Back to shows</button>
      </div>

      <div>
        <h2 style={{ margin: 0 }}>{seatMap.show.title}</h2>
        <p className="muted" style={{ margin: "4px 0 0" }}>
          {seatMap.show.venue} · {formatDate(seatMap.show.starts_at)}
        </p>
      </div>

      <div className="legend">
        <span><i style={{ background: "#d1fae5", borderColor: "#10b981" }} /> Available</span>
        <span><i style={{ background: "#4f46e5", borderColor: "#4f46e5" }} /> Your hold</span>
        <span><i style={{ background: "#fef3c7", borderColor: "#f59e0b" }} /> Held by someone</span>
        <span><i style={{ background: "#e5e7eb", borderColor: "#d1d5db" }} /> Booked</span>
      </div>

      <div className="screen">{FRONT_LABEL[seatMap.show.category] || "FRONT"}</div>

      <div className="seat-rows">
        {Object.entries(rows).map(([rowLabel, seats]) => (
          <div className="seat-row" key={rowLabel}>
            <span className="row-label">{rowLabel}</span>
            {seats.map((seat) => {
              const colour = colourOf(seat);
              return (
                <button
                  key={seat.id}
                  className={`seat ${colour}`}
                  title={`${seat.label} · ${rupees(seat.price_paise)}`}
                  disabled={busy || (colour !== "available" && colour !== "mine")}
                  onClick={() => handleSeatClick(seat)}
                >
                  {seat.seat_number}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {myHeldIds.length > 0 && (
        <div className="summary">
          <span>
            Holding <strong>{myHeldSeats.map((seat) => seat.label).join(", ")}</strong> ·{" "}
            {rupees(totalPaise)}
          </span>
          <span className="timer">⏱ {formatCountdown(soonestExpiry - now)}</span>
          <span className="spacer" />
          <button className="primary" onClick={handleBook} disabled={busy}>
            Book {myHeldIds.length} seat{myHeldIds.length > 1 ? "s" : ""} ({rupees(totalPaise)})
          </button>
        </div>
      )}

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}
    </div>
  );
}