import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, API_BASE, mediaUrl } from "../api";
import Navbar from "../components/Navbar";

function GoogleIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

function CompanyMark({ name, logoPath }) {
  const [failed, setFailed] = useState(false);
  const src = logoPath ? mediaUrl(logoPath) : null;
  if (!src || failed) {
    return (
      <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-white/15 text-lg font-bold text-white ring-1 ring-white/25">
        {name?.trim()?.[0] ?? "?"}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt=""
      className="h-14 w-14 rounded-xl object-cover ring-1 ring-white/25"
      onError={() => setFailed(true)}
    />
  );
}

export default function Landing() {
  const [companies, setCompanies] = useState([]);

  useEffect(() => {
    api.get("/jobs/companies").then((res) => setCompanies(res.data)).catch(() => setCompanies([]));
  }, []);

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary via-[#003d8a] to-[#001a3d] text-white">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(250,204,21,0.12),_transparent_50%)]" />
        <div className="relative mx-auto max-w-6xl px-4 py-20 text-center md:py-28">
          <p className="text-sm font-semibold uppercase tracking-widest text-accent">SeekJob job market</p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
            Find work that fits your next chapter
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-white/85">
            SeekJob connects talent with trusted employers across the metro: curated listings, one profile, and a
            clear view of every application you send.
          </p>

          {/* Primary CTAs */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/jobs"
              className="rounded-lg bg-accent px-8 py-3.5 font-semibold text-ink shadow-lg shadow-black/20 hover:brightness-95"
            >
              Search jobs
            </Link>
            <Link
              to="/register/applicant"
              className="rounded-lg border-2 border-white/80 bg-white/10 px-8 py-3.5 font-semibold text-white backdrop-blur-sm hover:bg-white/20"
            >
              Create applicant account
            </Link>
          </div>

          {/* OAuth quick sign-in */}
          <div className="mt-6 flex flex-col items-center gap-3">
            <div className="flex items-center gap-3 text-white/50">
              <span className="h-px w-20 bg-white/20" />
              <span className="text-xs font-medium uppercase tracking-wider">or sign in with</span>
              <span className="h-px w-20 bg-white/20" />
            </div>
            <div className="flex flex-wrap justify-center gap-3">
              <a
                href={`${API_BASE}/applicant/auth/google`}
                className="flex items-center gap-2.5 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-gray-700 shadow-lg shadow-black/20 transition hover:bg-gray-50"
              >
                <GoogleIcon />
                Continue with Google
              </a>
              <a
                href={`${API_BASE}/applicant/auth/github`}
                className="flex items-center gap-2.5 rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-black/20 transition hover:bg-gray-800"
              >
                <GitHubIcon />
                Continue with GitHub
              </a>
            </div>
            <p className="text-xs text-white/50">
              New? We'll collect your profile details right after — takes 30 seconds.
            </p>
          </div>

          <p className="mt-6 text-sm text-white/70">
            Hiring?{" "}
            <Link to="/register/company" className="font-semibold text-accent underline-offset-2 hover:underline">
              Register your company
            </Link>
          </p>
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────────── */}
      <section className="border-b border-gray-200 bg-white py-10">
        <div className="mx-auto flex max-w-6xl flex-wrap justify-center gap-10 px-4 text-center md:gap-16">
          <div>
            <p className="text-3xl font-bold text-primary">50+</p>
            <p className="text-sm font-medium text-gray-600">Open roles</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-primary">6</p>
            <p className="text-sm font-medium text-gray-600">Featured employers</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-primary">10</p>
            <p className="text-sm font-medium text-gray-600">Sample candidate profiles</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-primary">1</p>
            <p className="text-sm font-medium text-gray-600">Application profile</p>
          </div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-center text-2xl font-bold text-primary md:text-3xl">How it works</h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-gray-600">
          Three straightforward steps from browsing to hiring conversations.
        </p>
        <ol className="mt-12 grid gap-8 md:grid-cols-3">
          <li className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-white">
              1
            </span>
            <h3 className="mt-4 text-lg font-semibold text-ink">Browse</h3>
            <p className="mt-2 text-sm text-gray-600">
              Filter by company, role type, and sort by freshness. Full job descriptions and employer context in
              one place.
            </p>
          </li>
          <li className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-white">
              2
            </span>
            <h3 className="mt-4 text-lg font-semibold text-ink">Apply</h3>
            <p className="mt-2 text-sm text-gray-600">
              Log in once, confirm your profile and CV on file, and submit in seconds. No duplicate forms per listing.
            </p>
          </li>
          <li className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-white">
              3
            </span>
            <h3 className="mt-4 text-lg font-semibold text-ink">Track</h3>
            <p className="mt-2 text-sm text-gray-600">
              Use My applications for status updates. Join discussions to learn from others in the community.
            </p>
          </li>
        </ol>
      </section>

      {/* ── Featured employers ────────────────────────────────────── */}
      <section className="border-t border-gray-200 bg-gray-50 py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-xl font-bold text-primary">Hiring on SeekJob right now</h2>
          <p className="mx-auto mt-2 max-w-lg text-center text-sm text-gray-600">
            From tech and finance to healthcare and media — explore live listings from these organizations.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-6 md:gap-10">
            {companies.length === 0
              ? [1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-14 w-14 animate-pulse rounded-xl bg-gray-200" aria-hidden />
                ))
              : companies.map((c) => (
                  <Link
                    key={c.id}
                    to="/jobs"
                    title={c.name}
                    className="transition hover:scale-105 hover:opacity-90"
                  >
                    <CompanyMark name={c.name} logoPath={c.logo_path} />
                  </Link>
                ))}
          </div>
          <p className="mt-10 text-center">
            <Link
              to="/jobs"
              className="inline-flex rounded-lg bg-primary px-6 py-2.5 font-semibold text-white hover:bg-[#002a66]"
            >
              View all jobs
            </Link>
          </p>
        </div>
      </section>
    </div>
  );
}
