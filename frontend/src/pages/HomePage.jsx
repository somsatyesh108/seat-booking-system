// HomePage.jsx - Hero slides, category shortcuts, rows of titles, and how seat holds work.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import HeroCarousel from "../components/HeroCarousel";
import TitleRow from "../components/TitleRow";
import { groupByTitle } from "../utils";
import "../styles/home.css";

export default function HomePage() {
  const [shows, setShows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listShows().then(setShows).catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="page-empty">{error}</p>;
  if (!shows) return <p className="page-loading">Loading what's on...</p>;

  const titles = groupByTitle(shows);
  const movies = titles.filter((item) => item.category === "movie");
  const events = titles.filter((item) => item.category === "event");
  const buses = titles.filter((item) => item.category === "bus");
  const featured = [movies[0], events[0], movies[1], buses[0]].filter(Boolean);

  return (
    <div className="container home-top">
      <HeroCarousel items={featured} />

      <nav className="quick-cats" aria-label="Browse by category">
        <Link className="quick-cat" to="/movies">
          <span className="quick-cat-icon" aria-hidden="true">🎬</span>
          <div>
            <strong>Movies</strong>
            <span>{movies.length} now showing</span>
          </div>
        </Link>
        <Link className="quick-cat" to="/events">
          <span className="quick-cat-icon" aria-hidden="true">🎤</span>
          <div>
            <strong>Events</strong>
            <span>{events.length} coming up</span>
          </div>
        </Link>
        <Link className="quick-cat" to="/buses">
          <span className="quick-cat-icon" aria-hidden="true">🚌</span>
          <div>
            <strong>Buses</strong>
            <span>{buses.length} routes from Bengaluru</span>
          </div>
        </Link>
      </nav>

      <TitleRow heading="Recommended movies" seeAllTo="/movies" items={movies} />

      <section className="promo">
        <div>
          <h2>Your seat is held for five minutes.</h2>
          <p>
            When you pick a seat, it's yours while you pay. If someone taps the same seat a moment
            later, they see it's taken. Two people can never book the same seat.
          </p>
        </div>
        <ol className="promo-steps">
          <li>
            <div>
              <strong>Pick your seats</strong>
              <span>Tap any free seat on the seat map.</span>
            </div>
          </li>
          <li>
            <div>
              <strong>We hold them for you</strong>
              <span>They're yours for five minutes, with a countdown.</span>
            </div>
          </li>
          <li>
            <div>
              <strong>Pay and you're in</strong>
              <span>Your ticket appears in My tickets straight away.</span>
            </div>
          </li>
        </ol>
      </section>

      <TitleRow heading="Events in Bengaluru" seeAllTo="/events" items={events} />
      <TitleRow heading="Popular bus routes" seeAllTo="/buses" items={buses} />
    </div>
  );
}