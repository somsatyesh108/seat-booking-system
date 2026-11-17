// App.jsx - All the pages (routes) of Bookify, and the shared layout around them.

import { useEffect } from "react";
import { Link, Outlet, Route, Routes, useLocation } from "react-router-dom";
import Footer from "./components/Footer";
import Header from "./components/Header";
import RequireAuth from "./components/RequireAuth";
import AuthPage from "./pages/AuthPage";
import CheckoutPage from "./pages/CheckoutPage";
import ConfirmationPage from "./pages/ConfirmationPage";
import HomePage from "./pages/HomePage";
import ListingPage from "./pages/ListingPage";
import ProfilePage from "./pages/ProfilePage";
import SeatSelectionPage from "./pages/SeatSelectionPage";
import TicketsPage from "./pages/TicketsPage";
import TitlePage from "./pages/TitlePage";
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

function NotFound() {
  return (
    <div className="container page-empty">
      <h1>This page doesn't exist</h1>
      <p>The link may be broken, or the page may have moved.</p>
      <Link className="btn btn-primary" to="/">Go to the home page</Link>
    </div>
  );
}

// Pages that need you to be signed in.
const privatePage = (page) => <RequireAuth>{page}</RequireAuth>;

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
        <Route path="shows/:showId/seats" element={privatePage(<SeatSelectionPage />)} />
        <Route path="checkout/:showId" element={privatePage(<CheckoutPage />)} />
        <Route path="booking/confirmed" element={privatePage(<ConfirmationPage />)} />
        <Route path="tickets" element={privatePage(<TicketsPage />)} />
        <Route path="profile" element={privatePage(<ProfilePage />)} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}