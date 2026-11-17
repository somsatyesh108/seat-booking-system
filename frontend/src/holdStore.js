// holdStore.js - Remembers which seats YOU are holding for each show, in this browser tab.
// sessionStorage survives a page refresh but is cleared when the tab is closed.
// The server (Redis) is still the real source of truth; this is only so the page remembers.

const keyFor = (showId) => `bookify:holds:${showId}`;

// Returns { seatId: expiresAt (ms) } for holds that have not expired yet.
export function loadHolds(showId) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(keyFor(showId)) || "{}");
    const now = Date.now();
    return Object.fromEntries(
      Object.entries(saved).filter(([, expiresAt]) => expiresAt > now)
    );
  } catch {
    return {}; // storage blocked or broken data: start fresh
  }
}

export function saveHolds(showId, holds) {
  try {
    if (Object.keys(holds).length === 0) {
      sessionStorage.removeItem(keyFor(showId));
    } else {
      sessionStorage.setItem(keyFor(showId), JSON.stringify(holds));
    }
  } catch {
    // storage blocked (e.g. some private modes): holds just won't survive a refresh
  }
}

export function clearHolds(showId) {
  saveHolds(showId, {});
}