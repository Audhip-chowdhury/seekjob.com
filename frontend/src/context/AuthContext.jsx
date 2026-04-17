import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [role, setRole] = useState(() => localStorage.getItem("seekjob_role"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("seekjob_token");
    const r = localStorage.getItem("seekjob_role");
    if (!token || !r) {
      setLoading(false);
      return;
    }
    const path = r === "company" ? "/company/me" : "/applicant/me";
    api
      .get(path)
      .then((res) => {
        setUser(res.data);
        setRole(r);
      })
      .catch(() => {
        logout();
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(token, r) {
    localStorage.setItem("seekjob_token", token);
    localStorage.setItem("seekjob_role", r);
    setRole(r);
    const path = r === "company" ? "/company/me" : "/applicant/me";
    const res = await api.get(path);
    setUser(res.data);
  }

  function logout() {
    localStorage.removeItem("seekjob_token");
    localStorage.removeItem("seekjob_role");
    setRole(null);
    setUser(null);
  }

  async function refreshProfile() {
    const r = localStorage.getItem("seekjob_role");
    if (!r) return;
    const path = r === "company" ? "/company/me" : "/applicant/me";
    const res = await api.get(path);
    setUser(res.data);
  }

  return (
    <AuthContext.Provider
      value={{ role, user, loading, login, logout, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
