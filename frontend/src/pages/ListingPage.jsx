// ListingPage.jsx - Movies, Events, Buses and Search results.
// Filters live in the address bar (?language=Kannada&genre=Drama&sort=price),
// so the back button works and links can be shared.

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import TitleCard from "../components/TitleCard";
import { groupByTitle } from "../utils";
import "../styles/listing.css";

const PAGES = {
  movie: { heading: "Movies in Bengaluru", noun: "movies", genreLabel: "Genre" },
  event: { heading: "Events in Bengaluru", noun: "events", genreLabel: "Type" },
  bus: { heading: "Buses from Bengaluru", noun: "routes", genreLabel: "Bus type" },
};

const unique = (values) => [...new Set(values)].sort();
const genresOf = (item) => item.genre.split(",").map((g) => g.trim()).filter(Boolean);

function FilterGroup({ title, options, value, onChange }) {
  if (options.length === 0) return null;
  return (
    <div className="filter-group">
      <h2>{title}</h2>
      <div className="filter-chips">
        {options.map((option) => (
          <button
            key={option}
            className="chip"
            aria-pressed={option === value}
            onClick={() => onChange(option === value ? "" : option)}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ListingPage({ category }) {
  const [shows, setShows] = useState(null);
  const [error, setError] = useState("");
  const [params, setParams] = useSearchParams();

  const query = params.get("q") || "";
  const language = params.get("language") || "";
  const genre = params.get("genre") || "";
  const sort = params.get("sort") || "date";

  useEffect(() => {
    api.listShows(category).then(setShows).catch((err) => setError(err.message));
  }, [category]);

  function updateParam(name, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    setParams(next, { replace: true });
  }

  function clearFilters() {
    setParams(query && !category ? { q: query } : {}, { replace: true });
  }

  if (error) return <p className="page-empty">{error}</p>;
  if (!shows) return <p className="page-loading">Loading...</p>;

  const page = PAGES[category];
  const all = groupByTitle(shows);
  const languages = unique(all.map((item) => item.language).filter(Boolean));
  const genres = unique(all.flatMap(genresOf));
  const text = query.trim().toLowerCase();

  let results = all.filter((item) => {
    if (language && item.language !== language) return false;
    if (genre && !genresOf(item).includes(genre)) return false;
    if (text) {
      const haystack = [item.title, item.genre, item.language, ...item.showtimes.map((s) => s.venue)]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(text)) return false;
    }
    return true;
  });

  if (sort === "price") {
    results = [...results].sort(
      (a, b) => (a.minPricePaise ?? Infinity) - (b.minPricePaise ?? Infinity)
    );
  } else if (sort === "name") {
    results = [...results].sort((a, b) => a.title.localeCompare(b.title));
  }

  const heading = page ? page.heading : query ? `Results for "${query}"` : "Search Bookify";
  const noun = page ? page.noun : "results";
  const hasFilters = Boolean(language || genre || (category && query));

  return (
    <div className="container listing">
      <header className="listing-head">
        <h1>{heading}</h1>
        <p className="listing-count">
          {results.length} {noun}
        </p>
      </header>

      {!category && (
        <form className="listing-search" role="search" onSubmit={(e) => e.preventDefault()}>
          <span aria-hidden="true">🔍</span>
          <input
            type="search"
            placeholder="Search for movies, events, buses or venues"
            aria-label="Search"
            value={query}
            onChange={(e) => updateParam("q", e.target.value)}
            autoFocus
          />
        </form>
      )}

      <div className="listing-layout">
        <aside className="filters" aria-label="Filters">
          <FilterGroup
            title="Language"
            options={languages}
            value={language}
            onChange={(value) => updateParam("language", value)}
          />
          <FilterGroup
            title={page ? page.genreLabel : "Genre or type"}
            options={genres}
            value={genre}
            onChange={(value) => updateParam("genre", value)}
          />
          {hasFilters && (
            <button className="btn btn-secondary btn-small" onClick={clearFilters}>
              Clear filters
            </button>
          )}
        </aside>

        <section aria-label="Results">
          <div className="listing-toolbar">
            <label>
              Sort by
              <select value={sort} onChange={(e) => updateParam("sort", e.target.value === "date" ? "" : e.target.value)}>
                <option value="date">Soonest first</option>
                <option value="price">Price: low to high</option>
                <option value="name">Name</option>
              </select>
            </label>
          </div>

          {results.length === 0 ? (
            <div className="listing-empty">
              <h2>Nothing matches yet</h2>
              <p>Try a different language or genre, or clear the filters.</p>
            </div>
          ) : (
            <div className="title-grid">
              {results.map((item) => (
                <TitleCard key={item.slug} item={item} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}