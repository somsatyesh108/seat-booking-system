// Header.jsx - Frosted top bar: logo, search, city, account menu, and category links.

import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/authContext";
import Logo from "./Logo";

const CATEGORIES = [
  { to: "/movies", label: "Movies" },
  { to: "/events", label: "Events" },
  { to: "/buses", label: "Buses" },
];

const linkClass = ({ isActive }) => `cat-link${isActive ? " active" : ""}`;

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function PinIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();

  // The search box shows the search from the address bar on /search, and is empty elsewhere.
  const urlQuery = location.pathname === "/search" ? params.get("q") || "" : "";
  const [query, setQuery] = useState(urlQuery);
  const [lastUrlQuery, setLastUrlQuery] = useState(urlQuery);
  if (urlQuery !== lastUrlQuery) {
    // The address changed (e.g. we left the search page): update the box to match.
    setLastUrlQuery(urlQuery);
    setQuery(urlQuery);
  }

  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close the account menu when the user clicks anywhere outside it.
  useEffect(() => {
    if (!menuOpen) return;
    function handleOutsideClick(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [menuOpen]);

  function handleSearch(event) {
    event.preventDefault();
    const text = query.trim();
    navigate(text ? `/search?q=${encodeURIComponent(text)}` : "/search");
  }

  function handleSignOut() {
    setMenuOpen(false);
    logout();
    navigate("/");
  }

  const initial = user ? user.full_name.trim().charAt(0).toUpperCase() : "";

  return (
    <header className="site-header">
      <div className="container header-top">
        <Link to="/" className="logo" aria-label="Bookify home">
          <Logo />
        </Link>

        <form className="header-search" role="search" onSubmit={handleSearch}>
          <SearchIcon />
          <input
            type="search"
            placeholder="Search for movies, events and buses"
            aria-label="Search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>

        <span className="header-spacer" />

        <span className="city">
          <PinIcon /> Bengaluru
        </span>

        {user ? (
          <div className="user-menu" ref={menuRef}>
            <button
              className="avatar-btn"
              aria-label="Account menu"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              {initial}
            </button>
            {menuOpen && (
              <div className="menu" role="menu">
                <div className="menu-head">
                  <strong>{user.full_name}</strong>
                  <small>{user.email}</small>
                </div>
                <Link className="menu-item" role="menuitem" to="/tickets" onClick={() => setMenuOpen(false)}>
                  My tickets
                </Link>
                <Link className="menu-item" role="menuitem" to="/profile" onClick={() => setMenuOpen(false)}>
                  Profile
                </Link>
                <button className="menu-item" role="menuitem" onClick={handleSignOut}>
                  Sign out
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link className="btn btn-primary btn-small" to="/login">
            Sign in
          </Link>
        )}
      </div>

      <nav className="container header-bottom" aria-label="Categories">
        {CATEGORIES.map((category) => (
          <NavLink key={category.to} to={category.to} className={linkClass}>
            {category.label}
          </NavLink>
        ))}
        <span className="header-spacer" />
        <NavLink to="/tickets" className={linkClass}>
          My tickets
        </NavLink>
      </nav>
    </header>
  );
}