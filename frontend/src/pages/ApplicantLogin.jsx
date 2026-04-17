import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

export default function ApplicantLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/applicant/login", { email, password });
      await login(data.access_token, data.role);
      navigate("/jobs");
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Login failed");
    }
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-md px-4 py-12">
        <h1 className="text-2xl font-bold text-primary">Applicant login</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-lg border bg-white p-6 shadow">
          {err && <p className="text-sm text-red-600">{err}</p>}
          <label className="block text-sm font-medium">
            Email
            <input
              type="email"
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input
              type="password"
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button
            type="submit"
            className="w-full rounded-lg bg-primary py-2 font-semibold text-white hover:bg-[#002a66]"
          >
            Sign in
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          New here? <Link to="/register/applicant" className="text-primary underline">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
