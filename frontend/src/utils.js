// utils.js - Small helper functions shared by many pages.

const LOCALE = "en-IN";
const TIME_ZONE = "Asia/Kolkata";

// ---------------- Dates and times (always shown in Indian time) ----------------

// "2026-12-05T13:30:00Z" -> "5 Dec 2026, 7:00 pm"
export function formatDate(isoText) {
  return new Date(isoText).toLocaleString(LOCALE, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: TIME_ZONE,
  });
}

// -> "Sat, 5 Dec"
export function formatDay(isoText) {
  return new Date(isoText).toLocaleDateString(LOCALE, {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone: TIME_ZONE,
  });
}

// -> "7:00 pm"
export function formatTime(isoText) {
  return new Date(isoText).toLocaleTimeString(LOCALE, {
    hour: "numeric",
    minute: "2-digit",
    timeZone: TIME_ZONE,
  });
}

// -> "2026-12-05" (used to group showtimes by day)
export function dayKey(isoText) {
  return new Date(isoText).toLocaleDateString("en-CA", { timeZone: TIME_ZONE });
}

// 142 -> "2h 22m"
export function formatDuration(minutes) {
  if (!minutes) return "";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours === 0) return `${rest}m`;
  return rest === 0 ? `${hours}h` : `${hours}h ${rest}m`;
}

// ---------------- Money ----------------

// 25000 paise -> "₹250"
export function rupees(paise) {
  return `₹${(paise / 100).toLocaleString(LOCALE, { maximumFractionDigits: 2 })}`;
}

// 0 -> "Free", 25000 -> "₹250"
export function priceLabel(paise) {
  return paise === 0 ? "Free" : rupees(paise);
}

// ---------------- Seat holds ----------------

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

// ---------------- Titles (one movie / route / event with many showtimes) ----------------

// "Orbit 9" -> "orbit-9"
export function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

// Turn a flat list of showtimes into titles, each with its showtimes and live totals.
export function groupByTitle(shows) {
  const titles = new Map();
  for (const show of shows) {
    const slug = slugify(show.title);
    if (!titles.has(slug)) {
      titles.set(slug, {
        slug,
        title: show.title,
        category: show.category,
        description: show.description,
        genre: show.genre,
        language: show.language,
        duration_minutes: show.duration_minutes,
        age_rating: show.age_rating,
        showtimes: [],
      });
    }
    titles.get(slug).showtimes.push(show);
  }

  return [...titles.values()]
    .map((item) => {
      const prices = item.showtimes
        .map((show) => show.min_price_paise)
        .filter((price) => price !== null && price !== undefined);
      return {
        ...item,
        seatsLeft: item.showtimes.reduce((sum, s) => sum + (s.seats_total - s.seats_booked), 0),
        minPricePaise: prices.length > 0 ? Math.min(...prices) : null,
        firstStart: item.showtimes[0].starts_at,
      };
    })
    .sort((a, b) => a.firstStart.localeCompare(b.firstStart));
}

// The small line under a title: "Sci-Fi, Thriller" for movies, "AC Sleeper, 6h" for buses.
export function subtitleOf(item) {
  if (item.category === "bus") {
    return [item.genre, formatDuration(item.duration_minutes)].filter(Boolean).join(", ");
  }
  return item.genre;
}

// Each title gets its own poster colours, worked out from its name (same name = same colours).
export function posterStyle(item) {
  let hue = 0;
  for (const character of item.title) {
    hue = (hue * 31 + character.charCodeAt(0)) % 360;
  }
  return {
    background: `linear-gradient(160deg, hsl(${hue} 70% 55%) 0%, hsl(${(hue + 35) % 360} 70% 30%) 55%, hsl(${(hue + 60) % 360} 60% 12%) 100%)`,
  };
}

export const CATEGORY_ICONS = { movie: "🎬", bus: "🚌", event: "🎤" };