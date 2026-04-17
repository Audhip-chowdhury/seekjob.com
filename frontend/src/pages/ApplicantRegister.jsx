import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

export default function ApplicantRegister() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [picture, setPicture] = useState(null);
  const [cv, setCv] = useState(null);
  const [err, setErr] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    if (!picture || !cv) {
      setErr("Profile picture and CV are required.");
      return;
    }
    const fd = new FormData();
    fd.append("name", name);
    fd.append("email", email);
    fd.append("password", password);
    fd.append("picture", picture);
    fd.append("cv", cv);
    try {
      const { data } = await api.post("/applicant/register", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await login(data.access_token, data.role);
      navigate("/jobs");
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : JSON.stringify(d) || "Registration failed");
    }
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-md px-4 py-12">
        <h1 className="text-2xl font-bold text-primary">Create applicant profile</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-lg border bg-white p-6 shadow">
          {err && <p className="text-sm text-red-600">{err}</p>}
          <label className="block text-sm font-medium">
            Full name
            <input
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
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
            Password (min 6 characters)
            <input
              type="password"
              required
              minLength={6}
              className="mt-1 w-full rounded border px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Profile picture (JPG/JPEG, max 5MB)
            <input
              type="file"
              accept=".jpg,.jpeg"
              required
              className="mt-1 w-full text-sm"
              onChange={(e) => setPicture(e.target.files?.[0] || null)}
            />
          </label>
          <label className="block text-sm font-medium">
            CV (PDF, max 2MB)
            <input
              type="file"
              accept=".pdf"
              required
              className="mt-1 w-full text-sm"
              onChange={(e) => setCv(e.target.files?.[0] || null)}
            />
          </label>
          <button
            type="submit"
            className="w-full rounded-lg bg-primary py-2 font-semibold text-white hover:bg-[#002a66]"
          >
            Register
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Have an account? <Link to="/login/applicant" className="text-primary underline">Login</Link>
        </p>
      </div>
    </div>
  );
}
