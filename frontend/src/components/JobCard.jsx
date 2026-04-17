import { useState } from "react";
import { Link } from "react-router-dom";
import { mediaUrl } from "../api";

function companyInitial(name) {
  if (!name || !name.trim()) return "?";
  return name.trim()[0].toUpperCase();
}

function LogoOrInitial({ logoPath, companyName, className }) {
  const [failed, setFailed] = useState(false);
  const src = logoPath ? mediaUrl(logoPath) : null;

  if (!src || failed) {
    return (
      <div
        className={`flex shrink-0 items-center justify-center rounded-md bg-primary/90 text-lg font-bold text-white ${className}`}
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
      className={`shrink-0 rounded-md object-cover ${className}`}
      onError={() => setFailed(true)}
    />
  );
}

export default function JobCard({ job }) {
  return (
    <li>
      <Link
        to={`/jobs/${job.id}`}
        className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:border-primary/30 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        <article className="flex gap-4">
          <LogoOrInitial
            logoPath={job.company_logo}
            companyName={job.company_name}
            className="h-14 w-14"
          />
          <div className="min-w-0 flex-1">
            <h2 className="text-lg font-semibold text-primary">{job.job_role}</h2>
            <p className="text-sm text-gray-600">{job.company_name}</p>
            <p className="mt-1 text-sm text-gray-500">{job.location}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="rounded bg-surface px-2 py-0.5 text-xs font-medium text-ink">
                {job.job_type}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(job.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </article>
      </Link>
    </li>
  );
}
