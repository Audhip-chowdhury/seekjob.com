import { Children, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, mediaUrl } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

function companyInitial(name) {
  if (!name || !name.trim()) return "?";
  return name.trim()[0].toUpperCase();
}

function HeaderLogo({ logoPath, companyName, className }) {
  const [failed, setFailed] = useState(false);
  const src = logoPath ? mediaUrl(logoPath) : null;
  if (!src || failed) {
    return (
      <div
        className={`flex shrink-0 items-center justify-center rounded-lg bg-primary text-2xl font-bold text-white ${className}`}
        aria-hidden
      >
        {companyInitial(companyName)}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt=""
      className={`shrink-0 rounded-lg object-cover ${className}`}
      onError={() => setFailed(true)}
    />
  );
}

function renderDescriptionBlock(block, index) {
  const lines = block.split("\n");
  const head = lines[0].trim();
  const tail = lines.slice(1).join("\n").trim();
  const bulletBody =
    tail &&
    tail.split("\n").every((ln) => !ln.trim() || ln.trim().startsWith("-"));

  const isJobTitleLine =
    lines.length === 1 && /[\u2014\u2013]/.test(head) && !head.trim().startsWith("-");
  if (isJobTitleLine) {
    return (
      <h2 key={index} className="text-2xl font-bold text-ink">
        {head}
      </h2>
    );
  }

  const known =
    head === "The Role" ||
    head === "What you'll do" ||
    head === "What we're looking for" ||
    head === "What we offer" ||
    head.startsWith("About ");

  if (!known) {
    return (
      <div key={index} className="whitespace-pre-wrap text-gray-700">
        {block}
      </div>
    );
  }

  return (
    <section key={index} className="space-y-3">
      <h3 className="border-b border-gray-200 pb-1 text-lg font-semibold text-primary">{head}</h3>
      {bulletBody ? (
        <ul className="list-inside list-disc space-y-2 text-gray-700">
          {tail.split("\n").map((ln, i) => {
            const t = ln.trim();
            if (!t.startsWith("-")) return null;
            return (
              <li key={i} className="pl-1 marker:text-accent">
                {t.replace(/^-\s*/, "")}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="whitespace-pre-wrap text-gray-700">{tail}</p>
      )}
    </section>
  );
}

function JobDescription({ text }) {
  const blocks = text
    .split(/\n\n+/)
    .map((b) => b.trim())
    .filter(Boolean);
  return (
    <div className="space-y-8">
      {blocks.map((block, i) => renderDescriptionBlock(block, i))}
    </div>
  );
}

function DetailSection({ title, children }) {
  const nodes = Children.toArray(children).filter(Boolean);
  if (nodes.length === 0) return null;
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold text-primary">{title}</h2>
      <div className="mt-3 space-y-3 text-gray-700">{nodes}</div>
    </section>
  );
}

function ParaBlock({ label, text }) {
  if (!text || !String(text).trim()) return null;
  return (
    <div>
      {label && <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</p>}
      <p className="mt-1 whitespace-pre-wrap">{text}</p>
    </div>
  );
}

function formatJobDate(iso) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleDateString(undefined, { dateStyle: "long" });
  } catch {
    return iso;
  }
}

function hasStructuredOverview(job) {
  return !!(job.job_summary_purpose || job.key_responsibilities || job.team_context);
}

export default function JobDetail() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [err, setErr] = useState("");
  const [applyModal, setApplyModal] = useState(null);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyErr, setApplyErr] = useState("");
  const [applySyncPassword, setApplySyncPassword] = useState("");
  const [alreadyApplied, setAlreadyApplied] = useState(false);
  const { role, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get(`/jobs/${id}`)
      .then((res) => setJob(res.data))
      .catch(() => setErr("Job not found"));
  }, [id]);

  useEffect(() => {
    if (role !== "applicant" || !id) {
      setAlreadyApplied(false);
      return;
    }
    api
      .get("/applicant/applications")
      .then((res) => {
        const list = Array.isArray(res.data) ? res.data : [];
        setAlreadyApplied(list.some((a) => String(a.job_id) === String(id)));
      })
      .catch(() => setAlreadyApplied(false));
  }, [role, id]);

  const showModal = applyModal === "confirm" || applyModal === "success";
  useEffect(() => {
    if (!showModal) return;
    const onKey = (e) => {
      if (e.key === "Escape") {
        setApplyModal(null);
        setApplyErr("");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showModal]);

  async function confirmApply() {
    setApplyErr("");
    const pwd = applySyncPassword.trim();
    if (pwd.length > 0 && pwd.length < 8) {
      setApplyErr("Password for recruitment sync must be at least 8 characters.");
      return;
    }
    setApplyLoading(true);
    try {
      const payload = pwd.length > 0 ? { password: pwd } : {};
      await api.post(`/jobs/${id}/apply`, payload);
      setApplySyncPassword("");
      setAlreadyApplied(true);
      setApplyModal("success");
    } catch (ex) {
      setApplyErr(
        typeof ex.response?.data?.detail === "string"
          ? ex.response.data.detail
          : ex.response?.data?.detail
            ? JSON.stringify(ex.response.data.detail)
            : "Could not apply",
      );
    } finally {
      setApplyLoading(false);
    }
  }

  function closeModal() {
    setApplyModal(null);
    setApplyErr("");
    setApplySyncPassword("");
  }

  if (err || !job) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">{err || "Loading…"}</p>
      </div>
    );
  }

  const cvHref = user?.cv_path ? mediaUrl(user.cv_path) : null;
  const picHref = user?.picture_path ? mediaUrl(user.picture_path) : null;

  return (
    <div className="min-h-screen">
      <Navbar />
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="apply-modal-title"
          onClick={closeModal}
        >
          <div
            className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            {applyModal === "confirm" && (
              <>
                <h2 id="apply-modal-title" className="text-xl font-bold text-ink">
                  Confirm your application
                </h2>
                <p className="mt-1 text-sm text-gray-600">
                  You are applying to <span className="font-semibold">{job.job_role}</span> at{" "}
                  {job.posting_company_name || job.company_name}.
                </p>
                <div className="mt-5 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Applicant profile (on file)
                  </p>
                  <div className="mt-3 flex gap-3">
                    {picHref ? (
                      <img src={picHref} alt="" className="h-14 w-14 rounded-lg object-cover" />
                    ) : (
                      <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-primary text-lg font-bold text-white">
                        {companyInitial(user?.name)}
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-semibold text-ink">{user?.name}</p>
                      <p className="truncate text-sm text-gray-600">{user?.email}</p>
                      {cvHref && (
                        <a
                          href={cvHref}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 inline-block text-sm font-medium text-primary hover:underline"
                        >
                          View CV (PDF)
                        </a>
                      )}
                    </div>
                  </div>
                </div>
                <label className="mt-4 block text-sm text-gray-700">
                  <span className="font-medium">Account password (optional)</span>
                  <span className="mb-1 block text-xs font-normal text-gray-500">
                    Used only for the linked recruitment system sync — not stored by SeekJob. If provided,
                    minimum 8 characters.
                  </span>
                  <input
                    type="password"
                    autoComplete="current-password"
                    value={applySyncPassword}
                    onChange={(e) => setApplySyncPassword(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="Leave blank if not required"
                  />
                </label>
                {applyErr && <p className="mt-3 text-sm text-red-600">{applyErr}</p>}
                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={applyLoading}
                    onClick={confirmApply}
                    className="rounded-lg bg-accent px-4 py-2.5 font-semibold text-ink shadow hover:brightness-95 disabled:opacity-60"
                  >
                    {applyLoading ? "Submitting…" : "Submit application"}
                  </button>
                  <button
                    type="button"
                    onClick={closeModal}
                    className="rounded-lg border border-gray-300 px-4 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}
            {applyModal === "success" && (
              <>
                <h2 id="apply-modal-title" className="text-xl font-bold text-ink">
                  Thank you for applying
                </h2>
                <p className="mt-3 text-gray-700">
                  Your application has been submitted successfully. Check{" "}
                  <strong>My applications</strong> for status updates.
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <Link
                    to="/applicant/applications"
                    className="rounded-lg bg-primary px-4 py-2.5 font-semibold text-white hover:bg-[#002a66]"
                    onClick={closeModal}
                  >
                    My applications
                  </Link>
                  <button
                    type="button"
                    onClick={closeModal}
                    className="rounded-lg border border-gray-300 px-4 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Close
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
      <article className="mx-auto max-w-3xl px-4 py-8">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-6 text-sm text-primary hover:underline"
        >
          ← Back to listings
        </button>
        <div className="flex gap-4 border-b border-gray-200 pb-6">
          <HeaderLogo
            logoPath={job.company_logo}
            companyName={job.posting_company_name || job.company_name}
            className="h-20 w-20"
          />
          <div>
            <h1 className="text-2xl font-bold text-ink">{job.job_role}</h1>
            <p className="text-lg text-primary">{job.posting_company_name || job.company_name}</p>
            <p className="text-gray-600">{job.location}</p>
            {(job.work_mode || job.employment_type || job.job_level_grade || job.department_team) && (
              <p className="mt-2 text-sm text-gray-600">
                {[job.department_team, job.job_level_grade, job.employment_type, job.work_mode].filter(Boolean).join(" · ")}
              </p>
            )}
            {job.number_of_openings != null && job.number_of_openings > 0 && (
              <p className="mt-1 text-sm text-gray-600">
                Openings: <span className="font-medium">{job.number_of_openings}</span>
                {job.job_code_requisition_id && (
                  <span className="ml-2">
                    · Req: <span className="font-mono text-sm">{job.job_code_requisition_id}</span>
                  </span>
                )}
              </p>
            )}
            <p className="mt-2 text-sm text-gray-500">
              Posted {new Date(job.created_at).toLocaleString()}
            </p>
            <span className="mt-2 inline-block rounded bg-surface px-2 py-1 text-sm font-medium">
              {job.job_type}
            </span>
          </div>
        </div>

        {hasStructuredOverview(job) && (
          <DetailSection title="Role overview">
            <ParaBlock label="Summary / purpose" text={job.job_summary_purpose} />
            <ParaBlock label="Key responsibilities" text={job.key_responsibilities} />
            <ParaBlock label="Team context" text={job.team_context} />
          </DetailSection>
        )}

        {!hasStructuredOverview(job) && (
          <section className="mt-8">
            <h2 className="sr-only">Job description</h2>
            <JobDescription text={job.description} />
          </section>
        )}

        {(job.min_education ||
          job.years_experience_required ||
          job.required_skills_tools ||
          job.preferred_skills_nice_to_have) && (
          <DetailSection title="Qualifications">
            <ParaBlock label="Minimum education" text={job.min_education} />
            <ParaBlock label="Experience" text={job.years_experience_required} />
            <ParaBlock label="Required skills / tools" text={job.required_skills_tools} />
            <ParaBlock label="Nice to have" text={job.preferred_skills_nice_to_have} />
          </DetailSection>
        )}

        {!job.required_skills_tools && !job.preferred_skills_nice_to_have && job.skills_required && (
          <section className="mt-10">
            <h2 className="text-lg font-semibold text-primary">Skills required</h2>
            <p className="mt-2 text-gray-700">{job.skills_required}</p>
          </section>
        )}

        {(job.salary_range_band || job.stock_esop_details || job.benefits_summary) && (
          <DetailSection title="Compensation & benefits">
            <ParaBlock label="Salary range / band" text={job.salary_range_band} />
            <ParaBlock label="Stock / ESOP" text={job.stock_esop_details} />
            <ParaBlock label="Benefits" text={job.benefits_summary} />
          </DetailSection>
        )}

        {(job.application_deadline || job.expected_joining_date) && (
          <DetailSection title="Hiring timeline">
            {job.application_deadline && (
              <p>
                <span className="font-semibold text-ink">Application deadline:</span>{" "}
                {formatJobDate(job.application_deadline)}
              </p>
            )}
            {job.expected_joining_date && (
              <p>
                <span className="font-semibold text-ink">Expected joining:</span>{" "}
                {formatJobDate(job.expected_joining_date)}
              </p>
            )}
          </DetailSection>
        )}

        {(job.company_description_mission || job.culture_values) && (
          <DetailSection title="Company & culture">
            <ParaBlock label="Mission / description" text={job.company_description_mission} />
            <ParaBlock label="Culture / values" text={job.culture_values} />
          </DetailSection>
        )}

        {hasStructuredOverview(job) && job.description && job.description.trim() && job.description.trim() !== "—" && (
          <section className="mt-8">
            <h2 className="text-lg font-semibold text-primary">Additional description</h2>
            <JobDescription text={job.description} />
          </section>
        )}
        <div className="mt-10 flex flex-wrap gap-4">
          {role === "applicant" && alreadyApplied && (
            <p className="flex items-center rounded-lg border border-green-200 bg-green-50 px-4 py-2.5 text-sm font-medium text-green-900">
              You have already applied to this job.
              <Link to="/applicant/applications" className="ml-3 font-semibold text-primary underline">
                View your applications
              </Link>
            </p>
          )}
          {role === "applicant" && !alreadyApplied && (
            <button
              type="button"
              onClick={() => {
                setApplyErr("");
                setApplyModal("confirm");
              }}
              className="rounded-lg bg-accent px-6 py-2.5 font-semibold text-ink shadow hover:brightness-95"
            >
              Apply for this job
            </button>
          )}
          {!role && (
            <Link
              to="/login/applicant"
              className="rounded-lg bg-primary px-6 py-2.5 font-semibold text-white hover:bg-[#002a66]"
            >
              Log in as applicant to apply
            </Link>
          )}
          <Link
            to="/jobs"
            className="rounded-lg border border-gray-300 px-6 py-2.5 font-medium hover:bg-gray-50"
          >
            All jobs
          </Link>
        </div>
      </article>
    </div>
  );
}
