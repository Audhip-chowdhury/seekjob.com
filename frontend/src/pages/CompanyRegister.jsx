import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

export default function CompanyRegister() {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [logo, setLogo] = useState(null);
  const [err, setErr] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    const fd = new FormData();
    fd.append("name", name);
    fd.append("location", location);
    fd.append("email", email);
    fd.append("password", password);
    if (logo) fd.append("logo", logo);
    try {
      const { data } = await api.post("/company/register", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await login(data.access_token, data.role);
      navigate("/company/create-job");
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : JSON.stringify(d) || "Registration failed");
    }
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-md px-4 py-12">
        <h1 className="text-2xl font-bold text-primary">Register your company</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-lg border bg-white p-6 shadow">
          {err && <p className="text-sm text-red-600">{err}</p>}
          <label className="block text-sm font-medium">
            Company name
            <input
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Location
            <input
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Company email
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
            Logo (optional, JPG/PNG, max 5MB)
            <input
              type="file"
              accept=".jpg,.jpeg,.png"
              className="mt-1 w-full text-sm"
              onChange={(e) => setLogo(e.target.files?.[0] || null)}
            />
          </label>
          <button
            type="submit"
            className="w-full rounded-lg bg-primary py-2 font-semibold text-white hover:bg-[#002a66]"
          >
            Create company account
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Already registered? <Link to="/login/company" className="text-primary underline">Login</Link>
        </p>
      </div>
    </div>
  );
}
