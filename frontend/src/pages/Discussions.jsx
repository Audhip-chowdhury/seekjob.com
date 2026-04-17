import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

export default function Discussions() {
  const [threads, setThreads] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [jobId, setJobId] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [filterJob, setFilterJob] = useState("");
  const [filterCo, setFilterCo] = useState("");
  const [err, setErr] = useState("");
  const { role } = useAuth();

  function load() {
    const params = {};
    if (filterJob) params.job_id = Number(filterJob);
    if (filterCo) params.company_id = Number(filterCo);
    return api.get("/discussions", { params }).then((res) => setThreads(res.data));
  }

  useEffect(() => {
    Promise.all([
      api.get("/jobs/companies"),
      api.get("/jobs", { params: { sort_by: "date_desc" } }),
    ]).then(([co, jo]) => {
      setCompanies(co.data);
      setJobs(jo.data.items || []);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    load()
      .catch(() => setThreads([]))
      .finally(() => setLoading(false));
  }, [filterJob, filterCo]);

  async function createThread(e) {
    e.preventDefault();
    setErr("");
    try {
      await api.post("/discussions", {
        title: title.trim() || "Discussion",
        body: body.trim(),
        job_id: jobId ? Number(jobId) : null,
        company_id: companyId ? Number(companyId) : null,
      });
      setTitle("");
      setBody("");
      setJobId("");
      setCompanyId("");
      await load();
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Failed to post");
    }
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-3xl font-bold text-primary">Community</h1>
        <p className="text-gray-600">Share interview experiences and ask for advice</p>

        <div className="mt-6 flex flex-wrap gap-4 rounded-lg border bg-white p-4 shadow-sm">
          <label className="text-sm">
            Filter by job tag
            <select
              className="ml-2 rounded border px-2 py-1"
              value={filterJob}
              onChange={(e) => setFilterJob(e.target.value)}
            >
              <option value="">All</option>
              {jobs.slice(0, 80).map((j) => (
                <option key={j.id} value={j.id}>
                  #{j.id} {j.job_role}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Filter by company tag
            <select
              className="ml-2 rounded border px-2 py-1"
              value={filterCo}
              onChange={(e) => setFilterCo(e.target.value)}
            >
              <option value="">All</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {role && (
          <form onSubmit={createThread} className="mt-8 space-y-4 rounded-lg border border-accent/30 bg-white p-6 shadow">
            <h2 className="font-semibold text-primary">Start a thread</h2>
            {err && <p className="text-sm text-red-600">{typeof err === "string" ? err : JSON.stringify(err)}</p>}
            <input
              className="w-full rounded border px-3 py-2"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              required
              className="w-full rounded border px-3 py-2"
              rows={4}
              placeholder="Your message…"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <div className="flex flex-wrap gap-4">
              <label className="text-sm">
                Tag job (optional)
                <select
                  className="ml-2 rounded border px-2 py-1"
                  value={jobId}
                  onChange={(e) => setJobId(e.target.value)}
                >
                  <option value="">—</option>
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.job_role}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                Tag company (optional)
                <select
                  className="ml-2 rounded border px-2 py-1"
                  value={companyId}
                  onChange={(e) => setCompanyId(e.target.value)}
                >
                  <option value="">—</option>
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button type="submit" className="rounded-lg bg-primary px-4 py-2 font-semibold text-white">
              Post
            </button>
          </form>
        )}
        {!role && (
          <p className="mt-6 rounded-lg bg-amber-50 p-4 text-sm text-amber-900">
            <Link to="/login/applicant" className="font-semibold underline">
              Log in
            </Link>{" "}
            as an applicant or company to post.
          </p>
        )}

        <ul className="mt-6 space-y-4">
          {loading ? (
            <li className="text-center text-gray-500">Loading…</li>
          ) : (
            threads.map((t) => (
              <li key={t.id}>
                <Link
                  to={`/discussions/${t.id}`}
                  className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-primary/35 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                >
                  <span className="block text-lg font-semibold text-primary">{t.title}</span>
                  <p className="mt-1 line-clamp-2 text-sm text-gray-600">{t.body}</p>
                  <p className="mt-2 text-xs text-gray-400">
                    {t.author_name} · {new Date(t.created_at).toLocaleString()}
                    {t.replies?.length > 0 && ` · ${t.replies.length} replies`}
                  </p>
                </Link>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
