// AuthProvider.jsx - Keeps track of the logged-in user and shares it with the whole app.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, clearToken, getToken, saveToken } from "../api";
import { AuthContext } from "./authContext";

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(() => Boolean(getToken()));

  // On page load: if a token is saved, ask the backend "who am I?"
  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => clearToken()) // expired or invalid token -> forget it
      .finally(() => setChecking(false));
  }, []);

  const login = useCallback(async (email, password) => {
    const { access_token } = await api.login(email, password);
    saveToken(access_token);
    const me = await api.me();
    setUser(me);
    return me;
  }, []);

  const signup = useCallback(
    async (fullName, email, password) => {
      await api.signup(email, fullName, password);
      return login(email, password); // log in straight after signing up
    },
    [login]
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, checking, login, signup, logout }),
    [user, checking, login, signup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}