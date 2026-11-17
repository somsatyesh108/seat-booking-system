// Footer.jsx - Links at the bottom of every page, plus an honest note about the project.

import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <h4>Explore</h4>
            <Link to="/movies">Movies</Link>
            <Link to="/events">Events</Link>
            <Link to="/buses">Buses</Link>
          </div>
          <div>
            <h4>Your account</h4>
            <Link to="/tickets">My tickets</Link>
            <Link to="/profile">Profile</Link>
            <Link to="/login">Sign in</Link>
          </div>
          <div>
            <h4>How Bookify works</h4>
            <span>Your seats are held for 5 minutes</span>
            <span>Two people can never book the same seat</span>
            <span>Every ticket lives in My tickets</span>
          </div>
          <div>
            <h4>About</h4>
            <a href="https://github.com/somsatyesh108/seat-booking-system" target="_blank" rel="noreferrer">
              Source code on GitHub
            </a>
            <span>Built by Som</span>
          </div>
        </div>
        <div className="footer-bottom">
          <span>Bookify is a portfolio project. Shows and venues are fictional, and no real payments are taken.</span>
          <span>Bengaluru, India</span>
        </div>
      </div>
    </footer>
  );
}