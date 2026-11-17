// authContext.js - A shared "noticeboard" that tells every page who is logged in.

import { createContext, useContext } from "react";

export const AuthContext = createContext(null);

// Any component can call useAuth() to get { user, checking, login, signup, logout }.
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return value;
}