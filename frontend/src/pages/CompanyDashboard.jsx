import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

const JOB_TYPES = ["Management", "HR", "Software Dev", "Ops"];
const EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract"];
const WORK_MODES = ["Onsite", "Remote", "Hybrid"];

function emptyCreateForm() {
  return {
    job_role: "",
    job_type: "Software Dev",
    location: "",
    description: "",
    skills_required: "",
    department_team: "",
    job_level_grade: "",
    employment_type: "",
    work_mode: "",
    number_of_openings: "1",
    job_code_requisition_id: "",
    job_summary_purpose: "",
    key_responsibilities: "",
    team_context: "",
    min_education: "",
    years_experience_required: "",
    required_skills_tools: "",
    preferred_skills_nice_to_have: "",
    salary_range_band: "",
    stock_esop_details: "",
    benefits_summary: "",
    application_deadline: "",
    expected_joining_date: "",
    posting_company_name: "",
    company_description_mission: "",
    culture_values: "",
  };
}

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function truncate(s, max = 80) {
  if (!s) return "—";
  const t = s.trim();
  return t.length <= max ? t : `${t.slice(0, max)}…`;
}

function Field({ label, children, className = "" }) {
  return (
    <label className={`block text-sm font-medium text-slate-700 ${className}`}>
      {label}
      {children}
    </label>
  );
}

function inputCls() {
  return "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary";
}

function Section({ title, children }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4">
      <h3 className="text-xs font-bold uppercase tracking-wide text-primary">{title}</h3>
      <div className="mt-4 space-y-4">{children}</div>
    </div>
  );
}

export default function CompanyDashboard() {
  const [activeTab, setActiveTab] = useState("view");
  const [f, setF] = useState(emptyCreateForm);
  const [err, setErr] = useState("");
  const { role, user } = useAuth();

  const setField = (key, value) => setF((prev) => ({ ...prev, [key]: value }));

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [sortBy, setSortBy] = useState("date_desc");
  const [dateFrom, setDateFrom] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchInput), 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const loadMyJobs = useCallback(async () => {
    if (role !== "company") return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (debouncedSearch.trim()) params.set("q", debouncedSearch.trim());
      if (filterType) params.set("job_type", filterType);
      params.set("status", filterStatus);
      params.set("sort_by", sortBy);
      if (dateFrom) params.set("date_from", `${dateFrom}T00:00:00`);
      const { data } = await api.get(`/jobs/mine?${params.toString()}`);
      setItems(data.items || []);
      setTotal(data.total ?? 0);
    } catch {
      toast.error("Could not load your job postings.");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [role, debouncedSearch, filterType, filterStatus, sortBy, dateFrom]);

  useEffect(() => {
    if (activeTab !== "view") return;
    loadMyJobs();
  }, [loadMyJobs, activeTab]);

  function buildPayload() {
    const n = parseInt(f.number_of_openings, 10);
    const payload = {
      job_role: f.job_role.trim(),
      job_type: f.job_type,
      location: f.location.trim(),
      description: f.description.trim(),
      skills_required: f.skills_required.trim(),
      department_team: f.department_team.trim() || null,
      job_level_grade: f.job_level_grade.trim() || null,
      employment_type: f.employment_type.trim() || null,
      work_mode: f.work_mode.trim() || null,
      number_of_openings: Number.isFinite(n) && n >= 1 ? n : 1,
      job_code_requisition_id: f.job_code_requisition_id.trim() || null,
      job_summary_purpose: f.job_summary_purpose.trim() || null,
      key_responsibilities: f.key_responsibilities.trim() || null,
      team_context: f.team_context.trim() || null,
      min_education: f.min_education.trim() || null,
      years_experience_required: f.years_experience_required.trim() || null,
      required_skills_tools: f.required_skills_tools.trim() || null,
      preferred_skills_nice_to_have: f.preferred_skills_nice_to_have.trim() || null,
      salary_range_band: f.salary_range_band.trim() || null,
      stock_esop_details: f.stock_esop_details.trim() || null,
      benefits_summary: f.benefits_summary.trim() || null,
      posting_company_name: f.posting_company_name.trim() || null,
      company_description_mission: f.company_description_mission.trim() || null,
      culture_values: f.culture_values.trim() || null,
    };
    if (f.application_deadline) payload.application_deadline = f.application_deadline;
    if (f.expected_joining_date) payload.expected_joining_date = f.expected_joining_date;
    return payload;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/jobs", buildPayload());
      toast.success(`Job #${data.id} published successfully — ${data.job_role}`, { duration: 5000 });
      setF(emptyCreateForm());
      setActiveTab("view");
    } catch (ex) {
      const detail = ex.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg || d).join(", ")
            : "Failed to create job";
      setErr(msg);
      toast.error(msg);
    }
  }

  function clearFilters() {
    setSearchInput("");
    setDebouncedSearch("");
    setFilterType("");
    setFilterStatus("all");
    setSortBy("date_desc");
    setDateFrom("");
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
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-2">
          <h1 className="text-3xl font-bold text-primary">Job postings</h1>
          <p className="mt-1 text-slate-600">
            Create openings and review everything your company has published.
          </p>
        </div>

        <div
          className="mt-6 flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-100/90 p-1.5 shadow-inner"
          role="tablist"
          aria-label="Job postings sections"
        >
          <button
            type="button"
            role="tab"
            id="tab-view"
            aria-selected={activeTab === "view"}
            aria-controls="panel-view"
            className={`min-w-[10rem] flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
              activeTab === "view"
                ? "bg-white text-primary shadow-sm ring-1 ring-slate-200/80"
                : "text-slate-600 hover:bg-white/60 hover:text-slate-900"
            }`}
            onClick={() => setActiveTab("view")}
          >
            View listings
          </button>
          <button
            type="button"
            role="tab"
            id="tab-create"
            aria-selected={activeTab === "create"}
            aria-controls="panel-create"
            className={`min-w-[10rem] flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
              activeTab === "create"
                ? "bg-white text-primary shadow-sm ring-1 ring-slate-200/80"
                : "text-slate-600 hover:bg-white/60 hover:text-slate-900"
            }`}
            onClick={() => {
              setActiveTab("create");
              setF((prev) =>
                prev.posting_company_name || !user?.name ? prev : { ...prev, posting_company_name: user.name }
              );
            }}
          >
            Create posting
          </button>
        </div>

        {activeTab === "create" && (
          <section
            id="panel-create"
            role="tabpanel"
            aria-labelledby="tab-create"
            className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold text-slate-900">Create a new opening</h2>
            <p className="mt-1 text-sm text-slate-500">
              Required: job title, category, and work location. Other fields help candidates and appear on the public
              listing.
            </p>
            <form onSubmit={onSubmit} className="mt-6 space-y-8">
              {err && (
                <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{err}</p>
              )}

              <Section title="Basic job info">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Job title">
                    <input
                      required
                      className={inputCls()}
                      value={f.job_role}
                      onChange={(e) => setField("job_role", e.target.value)}
                    />
                  </Field>
                  <Field label="Category (internal)">
                    <select
                      required
                      className={inputCls()}
                      value={f.job_type}
                      onChange={(e) => setField("job_type", e.target.value)}
                    >
                      {JOB_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </Field>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Department / team">
                    <input className={inputCls()} value={f.department_team} onChange={(e) => setField("department_team", e.target.value)} />
                  </Field>
                  <Field label="Job level / grade (e.g. L3, Senior)">
                    <input className={inputCls()} value={f.job_level_grade} onChange={(e) => setField("job_level_grade", e.target.value)} />
                  </Field>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Employment type">
                    <select className={inputCls()} value={f.employment_type} onChange={(e) => setField("employment_type", e.target.value)}>
                      <option value="">Select…</option>
                      {EMPLOYMENT_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Work mode">
                    <select className={inputCls()} value={f.work_mode} onChange={(e) => setField("work_mode", e.target.value)}>
                      <option value="">Select…</option>
                      {WORK_MODES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </Field>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Location (city / site)">
                    <input
                      required
                      className={inputCls()}
                      placeholder="e.g. Nova Meridian — Hybrid"
                      value={f.location}
                      onChange={(e) => setField("location", e.target.value)}
                    />
                  </Field>
                  <Field label="Number of openings">
                    <input
                      type="number"
                      min={1}
                      className={inputCls()}
                      value={f.number_of_openings}
                      onChange={(e) => setField("number_of_openings", e.target.value)}
                    />
                  </Field>
                </div>
                <Field label="Job code / requisition ID">
                  <input className={inputCls()} value={f.job_code_requisition_id} onChange={(e) => setField("job_code_requisition_id", e.target.value)} />
                </Field>
              </Section>

              <Section title="Role overview">
                <Field label="Job summary / purpose">
                  <textarea rows={4} className={inputCls()} value={f.job_summary_purpose} onChange={(e) => setField("job_summary_purpose", e.target.value)} />
                </Field>
                <Field label="Key responsibilities">
                  <textarea rows={5} className={inputCls()} value={f.key_responsibilities} onChange={(e) => setField("key_responsibilities", e.target.value)} />
                </Field>
                <Field label="Team context / how the role fits">
                  <textarea rows={3} className={inputCls()} value={f.team_context} onChange={(e) => setField("team_context", e.target.value)} />
                </Field>
                <Field label="Combined description (optional)">
                  <textarea
                    rows={4}
                    className={inputCls()}
                    placeholder="Optional full narrative. If empty, a summary is built from the fields above."
                    value={f.description}
                    onChange={(e) => setField("description", e.target.value)}
                  />
                </Field>
              </Section>

              <Section title="Qualifications">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Minimum education">
                    <input className={inputCls()} value={f.min_education} onChange={(e) => setField("min_education", e.target.value)} />
                  </Field>
                  <Field label="Years of experience required">
                    <input className={inputCls()} placeholder="e.g. 3–5 years" value={f.years_experience_required} onChange={(e) => setField("years_experience_required", e.target.value)} />
                  </Field>
                </div>
                <Field label="Required skills / tools">
                  <textarea rows={3} className={inputCls()} value={f.required_skills_tools} onChange={(e) => setField("required_skills_tools", e.target.value)} />
                </Field>
                <Field label="Nice-to-have / preferred skills">
                  <textarea rows={3} className={inputCls()} value={f.preferred_skills_nice_to_have} onChange={(e) => setField("preferred_skills_nice_to_have", e.target.value)} />
                </Field>
                <Field label="Legacy “skills required” line (optional)">
                  <textarea
                    rows={2}
                    className={inputCls()}
                    placeholder="Optional; defaults to required skills / tools if empty."
                    value={f.skills_required}
                    onChange={(e) => setField("skills_required", e.target.value)}
                  />
                </Field>
              </Section>

              <Section title="Compensation & benefits">
                <Field label="Salary range / band">
                  <input className={inputCls()} value={f.salary_range_band} onChange={(e) => setField("salary_range_band", e.target.value)} />
                </Field>
                <Field label="Stock / ESOP details">
                  <textarea rows={2} className={inputCls()} value={f.stock_esop_details} onChange={(e) => setField("stock_esop_details", e.target.value)} />
                </Field>
                <Field label="Benefits (health, PF, leaves, etc.)">
                  <textarea rows={3} className={inputCls()} value={f.benefits_summary} onChange={(e) => setField("benefits_summary", e.target.value)} />
                </Field>
              </Section>

              <Section title="Hiring process">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Application deadline">
                    <input type="date" className={inputCls()} value={f.application_deadline} onChange={(e) => setField("application_deadline", e.target.value)} />
                  </Field>
                  <Field label="Expected joining date">
                    <input type="date" className={inputCls()} value={f.expected_joining_date} onChange={(e) => setField("expected_joining_date", e.target.value)} />
                  </Field>
                </div>
              </Section>

              <Section title="Company & culture">
                <Field label="Company name (on this posting)">
                  <input className={inputCls()} placeholder="Defaults from your account if empty" value={f.posting_company_name} onChange={(e) => setField("posting_company_name", e.target.value)} />
                </Field>
                <Field label="Company description / mission">
                  <textarea rows={3} className={inputCls()} value={f.company_description_mission} onChange={(e) => setField("company_description_mission", e.target.value)} />
                </Field>
                <Field label="Culture / values">
                  <textarea rows={3} className={inputCls()} value={f.culture_values} onChange={(e) => setField("culture_values", e.target.value)} />
                </Field>
              </Section>

              <button type="submit" className="rounded-lg bg-primary px-6 py-2.5 font-semibold text-white shadow hover:opacity-95">
                Publish opening
              </button>
            </form>
          </section>
        )}

        {activeTab === "view" && (
          <section
            id="panel-view"
            role="tabpanel"
            aria-labelledby="tab-view"
            className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Your listings</h2>
                <p className="text-sm text-slate-600">
                  {loading ? "Loading…" : `${total} job${total === 1 ? "" : "s"} match your filters`}
                </p>
              </div>
              <button
                type="button"
                onClick={clearFilters}
                className="self-start rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Clear filters
              </button>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
              <Field label="Search">
                <input
                  type="search"
                  placeholder="Role, location, skills…"
                  className={inputCls()}
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                />
              </Field>
              <Field label="Job type">
                <select className={inputCls()} value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                  <option value="">All types</option>
                  {JOB_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Listing status">
                <select className={inputCls()} value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                  <option value="all">Active & inactive</option>
                  <option value="active">Active only</option>
                  <option value="inactive">Inactive only</option>
                </select>
              </Field>
              <Field label="Sort by date">
                <select className={inputCls()} value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                  <option value="date_desc">Newest first</option>
                  <option value="date_asc">Oldest first</option>
                </select>
              </Field>
              <Field label="Posted on or after">
                <input type="date" className={inputCls()} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
              </Field>
            </div>

            <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-100 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  <tr>
                    <th className="whitespace-nowrap px-4 py-3">Job ID</th>
                    <th className="min-w-[10rem] px-4 py-3">Role</th>
                    <th className="whitespace-nowrap px-4 py-3">Type</th>
                    <th className="min-w-[8rem] px-4 py-3">Location</th>
                    <th className="whitespace-nowrap px-4 py-3">Status</th>
                    <th className="whitespace-nowrap px-4 py-3 text-right">Applicants</th>
                    <th className="whitespace-nowrap px-4 py-3">Posted</th>
                    <th className="min-w-[12rem] px-4 py-3">Skills (preview)</th>
                    <th className="whitespace-nowrap px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {loading ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-12 text-center text-slate-500">
                        Loading your jobs…
                      </td>
                    </tr>
                  ) : items.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-12 text-center text-slate-500">
                        No jobs match these filters. Add one under Create posting or adjust filters.
                      </td>
                    </tr>
                  ) : (
                    items.map((job) => (
                      <tr key={job.id} className="hover:bg-slate-50/80">
                        <td className="whitespace-nowrap px-4 py-3 font-mono font-medium text-primary">#{job.id}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{job.job_role}</td>
                        <td className="whitespace-nowrap px-4 py-3 text-slate-700">{job.job_type}</td>
                        <td className="px-4 py-3 text-slate-700">{job.location}</td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                              job.is_active ? "bg-emerald-100 text-emerald-800" : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {job.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums text-slate-800">
                          {job.application_count ?? 0}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-slate-600">{formatDate(job.created_at)}</td>
                        <td
                          className="max-w-[14rem] px-4 py-3 text-slate-600"
                          title={job.required_skills_tools || job.skills_required}
                        >
                          {truncate(job.required_skills_tools || job.skills_required, 100)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <Link to={`/jobs/${job.id}`} className="font-medium text-primary underline hover:text-primary/80">
                            View listing
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
