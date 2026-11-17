// TitlePage.jsx - One movie, bus route or event: banner, about, and showtimes by date and venue.

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import Poster from "../components/Poster";
import TitleRow from "../components/TitleRow";
import {
  dayKey,
  formatDay,
  formatDuration,
  formatTime,
  groupByTitle,
  posterStyle,
  priceLabel,
} from "../utils";
import "../styles/title.css";

const KIND = { movie: "Movie", bus: "Bus route", event: "Event" };
const RELATED_HEADING = { movie: "You may also like", bus: "More routes", event: "More events" };
const FILLING_FAST_AT = 20; // seats left

export default function TitlePage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [titles, setTitles] = useState(null);
  const [error, setError] = useState("");
  const [chosenDay, setChosenDay] = useState(null);

  useEffect(() => {
    api
      .listShows()
      .then((shows) => setTitles(groupByTitle(shows)))
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="page-empty">{error}</p>;
  if (!titles) return <p className="page-loading">Loading...</p>;

  const item = titles.find((title) => title.slug === slug);
  if (!item) {
    return (
      <div className="container page-empty">
        <h1>We couldn't find that title</h1>
        <p>It may have finished its run.</p>
        <Link className="btn btn-primary" to="/">Browse what's on</Link>
      </div>
    );
  }

  // Dates that have showtimes, e.g. ["2026-11-20", "2026-11-21"]
  const days = [...new Set(item.showtimes.map((show) => dayKey(show.starts_at)))];
  const activeDay = days.includes(chosenDay) ? chosenDay : days[0];

  // That day's showtimes, grouped by venue: { "Lumiere Cinemas, Koramangala": [show, show] }
  const byVenue = new Map();
  item.showtimes
    .filter((show) => dayKey(show.starts_at) === activeDay)
    .forEach((show) => {
      if (!byVenue.has(show.venue)) byVenue.set(show.venue, []);
      byVenue.get(show.venue).push(show);
    });

  const facts = [item.genre, item.language, formatDuration(item.duration_minutes), item.age_rating]
    .filter(Boolean);
  const related = titles.filter((title) => title.category === item.category && title.slug !== item.slug);
  const isBus = item.category === "bus";

  return (
    <>
      <section className="title-banner" style={posterStyle(item)}>
        <div className="container title-banner-inner">
          <Poster item={item} />
          <div className="title-info">
            <span className="title-kind">{KIND[item.category]}</span>
            <h1>{item.title}</h1>
            <ul className="title-facts">
              {facts.map((fact) => (
                <li key={fact}>{fact}</li>
              ))}
            </ul>
            <p className="title-price">
              {item.minPricePaise === 0 ? "Free entry" : `Tickets from ${priceLabel(item.minPricePaise)}`}
            </p>
            <a className="btn btn-light btn-large" href="#showtimes">
              {isBus ? "Book seats" : "Book tickets"}
            </a>
          </div>
        </div>
      </section>

      <div className="container">
        <section className="title-section">
          <h2>About</h2>
          <p className="title-about">{item.description || "Details coming soon."}</p>
        </section>

        <section className="title-section" id="showtimes">
          <h2>{isBus ? "Departures" : "Showtimes"}</h2>

          <div className="day-tabs" role="group" aria-label="Choose a date">
            {days.map((day) => {
              const firstThatDay = item.showtimes.find((show) => dayKey(show.starts_at) === day);
              return (
                <button
                  key={day}
                  className="day-tab"
                  aria-pressed={day === activeDay}
                  onClick={() => setChosenDay(day)}
                >
                  {formatDay(firstThatDay.starts_at)}
                </button>
              );
            })}
          </div>

          {[...byVenue.entries()].map(([venue, shows]) => (
            <div className="venue" key={venue}>
              <div className="venue-name">
                <strong>{venue}</strong>
                <span>{isBus ? "Boarding point" : "Bengaluru"}</span>
              </div>
              <div className="times">
                {shows.map((show) => {
                  const seatsLeft = show.seats_total - show.seats_booked;
                  const soldOut = seatsLeft === 0;
                  const fillingFast = !soldOut && seatsLeft <= FILLING_FAST_AT;
                  return (
                    <button
                      key={show.id}
                      className={`time-btn${fillingFast ? " is-filling" : ""}`}
                      disabled={soldOut}
                      onClick={() => navigate(`/shows/${show.id}/seats`)}
                    >
                      <span>{formatTime(show.starts_at)}</span>
                      <small>
                        {soldOut
                          ? "Sold out"
                          : fillingFast
                            ? `${seatsLeft} left`
                            : show.min_price_paise === 0
                              ? "Free"
                              : `from ${priceLabel(show.min_price_paise)}`}
                      </small>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          <p className="times-note">Times in orange are filling fast. Your seats are held for 5 minutes once you pick them.</p>
        </section>

        <TitleRow heading={RELATED_HEADING[item.category]} items={related} />
      </div>
    </>
  );
}