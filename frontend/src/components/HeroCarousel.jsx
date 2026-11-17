// HeroCarousel.jsx - Big featured slides that change every 6 seconds.
// Pauses while the mouse or keyboard focus is on it, and never auto-plays
// for people who turned off animations in their system settings.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { formatDuration, posterStyle } from "../utils";

const SLIDE_EVERY_MS = 6000;
const KICKERS = { movie: "Now showing", event: "Live in Bengaluru", bus: "Popular route" };

export default function HeroCarousel({ items }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const count = items.length;

  useEffect(() => {
    if (paused || count < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = setInterval(() => setIndex((current) => (current + 1) % count), SLIDE_EVERY_MS);
    return () => clearInterval(timer);
  }, [paused, count]);

  if (count === 0) return null;

  const goTo = (next) => setIndex((next + count) % count);

  return (
    <section
      className="hero"
      aria-roledescription="carousel"
      aria-label="Featured"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div className="hero-track" style={{ transform: `translateX(-${index * 100}%)` }}>
        {items.map((item, slideIndex) => {
          const isCurrent = slideIndex === index;
          return (
            <article
              key={item.slug}
              className="hero-slide"
              style={posterStyle(item)}
              aria-roledescription="slide"
              aria-label={`${slideIndex + 1} of ${count}`}
              aria-hidden={!isCurrent}
            >
              <div className="hero-content">
                <span className="hero-kicker">{KICKERS[item.category]}</span>
                <h2>{item.title}</h2>
                <p>{item.description}</p>
                <p className="hero-meta">
                  {[item.genre, item.language, formatDuration(item.duration_minutes), item.age_rating]
                    .filter(Boolean)
                    .join("  |  ")}
                </p>
                <Link
                  className="btn btn-light btn-large"
                  to={`/title/${item.slug}`}
                  tabIndex={isCurrent ? 0 : -1}
                >
                  {item.category === "bus" ? "Book seats" : "Book tickets"}
                </Link>
              </div>
            </article>
          );
        })}
      </div>

      <button className="hero-arrow prev" aria-label="Previous slide" onClick={() => goTo(index - 1)}>
        ‹
      </button>
      <button className="hero-arrow next" aria-label="Next slide" onClick={() => goTo(index + 1)}>
        ›
      </button>

      <div className="hero-dots">
        {items.map((item, dotIndex) => (
          <button
            key={item.slug}
            aria-label={`Show slide ${dotIndex + 1}`}
            aria-current={dotIndex === index}
            onClick={() => setIndex(dotIndex)}
          />
        ))}
      </div>
    </section>
  );
}