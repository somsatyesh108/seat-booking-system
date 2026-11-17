// utils.js - Small helper functions shared by several pages.

// "2026-12-05T13:30:00Z" -> "5 Dec 2026, 7:00 pm" (shown in Indian time)
export function formatDate(isoText) {
  return new Date(isoText).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Kolkata",
  });
}

// 25000 paise -> "₹250"
export function rupees(paise) {
  return `₹${(paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

// 299000 ms -> "4:59"
export function formatCountdown(ms) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

// 300 -> the exact time (in ms) that is 300 seconds from now
export function expiresAtFromNow(seconds) {
  return Date.now() + seconds * 1000;
}