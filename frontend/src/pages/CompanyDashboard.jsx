import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

const JOB_TYPES = ["Management", "HR", "Software Dev", "Ops"];

export default function CompanyDashboard() {
  const [jobRole, setJobRole] = useState("");
  const [jobType, setJobType] = useState("Software Dev");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const { role } = useAuth();

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    try {
      await api.post("/jobs", {
        job_role: jobRole,
        job_type: jobType,
        location,
        description,
        skills_required: skills,
      });
      setMsg("Job posted successfully.");
      setJobRole("");
      setLocation("");
      setDescription("");
      setSkills("");
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Failed to create job");
    }
  }

  if (role !== "company") {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">
          <Link to="/login/company" className="text-primary underline">
            Sign in as a company
          </Link>{" "}
          to post jobs.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-2xl px-4 py-8">
        <h1 className="text-3xl font-bold text-primary">Create job opening</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-lg border bg-white p-6 shadow">
          {err && <p className="text-sm text-red-600">{typeof err === "string" ? err : JSON.stringify(err)}</p>}
          {msg && <p className="text-sm text-green-700">{msg}</p>}
          <label className="block text-sm font-medium">
            Job role
            <input
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={jobRole}
              onChange={(e) => setJobRole(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Job type
            <select
              className="mt-1 w-full rounded border px-3 py-2"
              value={jobType}
              onChange={(e) => setJobType(e.target.value)}
            >
              {JOB_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
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
            Detailed job description
            <textarea
              required
              rows={8}
              className="mt-1 w-full rounded border px-3 py-2"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Skills required
            <textarea
              required
              rows={3}
              className="mt-1 w-full rounded border px-3 py-2"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
            />
          </label>
          <button type="submit" className="rounded-lg bg-primary px-6 py-2.5 font-semibold text-white">
            Publish opening
          </button>
        </form>
      </div>
    </div>
  );
}
