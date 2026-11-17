// RequireAuth.jsx - A guard: pages wrapped in this need login. Visitors are sent to /login,
// and come back to the same page after logging in.

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/authContext";

export default function RequireAuth({ children }) {
  const { user, checking } = useAuth();
  const location = useLocation();

  if (checking) return <p className="page-loading">Loading...</p>;
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return children;
}