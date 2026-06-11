import axios from "axios";
import { createContext, useContext, useState } from "react";

// One axios instance; attaches the bearer token on every request.
export const api = axios.create({ baseURL: "" });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => ({
    token: localStorage.getItem("token"),
    role: localStorage.getItem("role"),
  }));

  async function login(username, password) {
    const { data } = await api.post("/api/auth/login", { username, password });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    setAuth({ token: data.access_token, role: data.role });
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    setAuth({ token: null, role: null });
  }

  return <AuthCtx.Provider value={{ ...auth, login, logout }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
export const canEdit = (role) => role === "editor" || role === "admin";

export const fmt = (n) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n || 0);
export const fmtPct = (n) => `${n > 0 ? "+" : ""}${(n || 0).toFixed(1)}%`;
