// ProfilePage.jsx - Your account: name, email, member since, booking stats, and sign out.

import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth/authContext";
import { rupees } from "../utils";
import "../styles/tickets.css";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.myBookings().then(setBookings).catch((err) => setError(err.message));
  }, []);

  function handleSignOut() {
    logout();
    navigate("/");
  }

  const initial = user.full_name.trim().charAt(0).toUpperCase();
  const memberSince = new Date(user.created_at).toLocaleDateString("en-IN", {
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
  const seatsBooked = bookings ? bookings.length : null;
  const showsBooked = bookings ? new Set(bookings.map((b) => b.show_id)).size : null;
  const totalSpent = bookings ? bookings.reduce((sum, b) => sum + b.amount_paise, 0) : null;

  return (
    <div className="container profile">
      <section className="profile-card">
        <span className="profile-avatar" aria-hidden="true">{initial}</span>
        <div>
          <h1>{user.full_name}</h1>
          <p>{user.email}</p>
          <p>Member since {memberSince}</p>
        </div>
      </section>

      {error && <p className="notice notice-error" style={{ marginTop: 24 }}>{error}</p>}

      <dl className="profile-stats">
        <div>
          <dt>Seats booked</dt>
          <dd>{seatsBooked ?? "..."}</dd>
        </div>
        <div>
          <dt>Shows and trips</dt>
          <dd>{showsBooked ?? "..."}</dd>
        </div>
        <div>
          <dt>Total spent</dt>
          <dd>{totalSpent === null ? "..." : rupees(totalSpent)}</dd>
        </div>
      </dl>

      <div className="profile-actions">
        <Link className="btn btn-primary" to="/tickets">View my tickets</Link>
        <button className="btn btn-outline" onClick={handleSignOut}>Sign out</button>
      </div>
    </div>
  );
}