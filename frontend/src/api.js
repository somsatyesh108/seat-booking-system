// api.js - One place for every call to our FastAPI backend.

const API_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "seat_booking_token";

// ---------- Saving the login token in the browser ----------
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------- One helper that every request goes through ----------
async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  let payload;

  if (form) {
    // Login uses a form (OAuth2 standard): username=...&password=...
    payload = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();
  if (auth && token) {
    headers["Authorization"] = `Bearer ${token}`; // our "wristband"
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { method, headers, body: payload });
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }

  if (response.status === 204) return null; // success with no body (e.g. release hold)

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    // FastAPI errors look like {"detail": "..."} or {"detail": [{"msg": "..."}]}
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(", ")
      : detail || `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

// ---------- Every endpoint our app uses ----------
export const api = {
  signup: (email, fullName, password) =>
    request("/auth/signup", {
      method: "POST",
      body: { email, full_name: fullName, password },
      auth: false,
    }),
  login: (email, password) =>
    request("/auth/login", {
      method: "POST",
      form: { username: email, password },
      auth: false,
    }),
  me: () => request("/auth/me"),
  listShows: () => request("/shows", { auth: false }),
  seatMap: (showId) => request(`/shows/${showId}/seats`, { auth: false }),
  holdSeat: (showId, seatId) =>
    request(`/shows/${showId}/seats/${seatId}/hold`, { method: "POST" }),
  releaseSeat: (showId, seatId) =>
    request(`/shows/${showId}/seats/${seatId}/hold`, { method: "DELETE" }),
  book: (showId, seatIds) =>
    request("/bookings", { method: "POST", body: { show_id: showId, seat_ids: seatIds } }),
  myBookings: () => request("/bookings/me"),
};