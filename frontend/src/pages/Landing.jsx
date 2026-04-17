import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, mediaUrl } from "../api";
import Navbar from "../components/Navbar";

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
          <p className="mt-6 text-sm text-white/70">
            Hiring?{" "}
            <Link to="/register/company" className="font-semibold text-accent underline-offset-2 hover:underline">
              Register your company
            </Link>
          </p>
        </div>
      </section>

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

      <section className="border-t border-gray-200 bg-gray-50 py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-xl font-bold text-primary">Hiring on SeekJob right now</h2>
          <p className="mx-auto mt-2 max-w-lg text-center text-sm text-gray-600">
            From tech and finance to healthcare and media — explore live listings from these organizations.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-6 md:gap-10">
            {companies.length === 0
              ? [1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="h-14 w-14 animate-pulse rounded-xl bg-gray-200"
                    aria-hidden
                  />
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
