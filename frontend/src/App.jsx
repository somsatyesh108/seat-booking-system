// App.jsx - All the pages (routes) of Bookify, and the shared layout around them.

import { useEffect, useState } from "react";
import {
  Link,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { api } from "./api";
import Footer from "./components/Footer";
import Header from "./components/Header";
import RequireAuth from "./components/RequireAuth";
import AuthPage from "./pages/AuthPage";
import HomePage from "./pages/HomePage";
import ListingPage from "./pages/ListingPage";
import MyBookingsPage from "./pages/MyBookingsPage";
import SeatMapPage from "./pages/SeatMapPage";
import TitlePage from "./pages/TitlePage";
import "./App.css"; // old page styles, kept until every page is redesigned
import "./styles/site.css";

// Header + page + footer, shared by every page except /login and /signup.
function Layout() {
  const { pathname } = useLocation();

  // Every time the address changes, start the new page at the top.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className="site">
      <Header />
      <main className="site-main">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

// ---- Temporary bridges: connect the old pages to the new URLs (replaced in later steps) ----

function OldSeatMapPage() {
  const { showId } = useParams();
  const navigate = useNavigate();
  const [show, setShow] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getShow(showId).then(setShow).catch((err) => setError(err.message));
  }, [showId]);

  if (error) return <p className="page-empty">{error}</p>;
  if (!show) return <p className="page-loading">Loading seats...</p>;
  return (
    <div className="container" style={{ paddingTop: 32 }}>
      <SeatMapPage show={show} onBack={() => navigate(-1)} />
    </div>
  );
}

function OldTicketsPage() {
  const navigate = useNavigate();
  return (
    <div className="container" style={{ paddingTop: 32 }}>
      <MyBookingsPage onBrowseShows={() => navigate("/")} />
    </div>
  );
}

function NotFound() {
  return (
    <div className="container page-empty">
      <h1>This page doesn't exist</h1>
      <p>The link may be broken, or the page may have moved.</p>
      <Link className="btn btn-primary" to="/">Go to the home page</Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage key="login" mode="login" />} />
      <Route path="/signup" element={<AuthPage key="signup" mode="signup" />} />

      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="title/:slug" element={<TitlePage />} />
        <Route path="movies" element={<ListingPage key="movie" category="movie" />} />
        <Route path="events" element={<ListingPage key="event" category="event" />} />
        <Route path="buses" element={<ListingPage key="bus" category="bus" />} />
        <Route path="search" element={<ListingPage key="search" />} />
        <Route
          path="shows/:showId/seats"
          element={<RequireAuth><OldSeatMapPage /></RequireAuth>}
        />
        <Route
          path="tickets"
          element={<RequireAuth><OldTicketsPage /></RequireAuth>}
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}