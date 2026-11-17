// Logo.jsx - The Bookify logo: a ticket-shaped tile (a notch on each side, like a real ticket)
// with a geometric "b", followed by the word "bookify".
// Colours follow the surroundings: the tile uses the current text colour (black on white
// pages, white on dark panels) and the "b" uses the opposite colour (--logo-contrast).

import { useId } from "react";

export default function Logo({ size = 30 }) {
  // A unique id, so two logos on one page never clash.
  const maskId = `bookify-ticket-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;

  return (
    <>
      <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
        <defs>
          {/* White = visible, black = cut out: the two side notches of a ticket */}
          <mask id={maskId}>
            <rect width="64" height="64" rx="16" fill="#fff" />
            <circle cx="0" cy="32" r="7" fill="#000" />
            <circle cx="64" cy="32" r="7" fill="#000" />
          </mask>
        </defs>
        {/* The tile takes the text colour around it */}
        <rect width="64" height="64" rx="16" fill="currentColor" mask={`url(#${maskId})`} />
        {/* The "b" takes the opposite colour */}
        <rect x="20" y="13" width="7" height="38" rx="3.5" style={{ fill: "var(--logo-contrast, #fff)" }} />
        <circle
          cx="34"
          cy="38"
          r="11"
          fill="none"
          strokeWidth="7"
          style={{ stroke: "var(--logo-contrast, #fff)" }}
        />
      </svg>
      bookify
    </>
  );
}