import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

// Shown while exchanging the OAuth token
function LoadingScreen() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-primary via-[#003d8a] to-[#001a3d]">
      <svg className="h-10 w-10 animate-spin text-white/60" fill="none" viewBox="0 0 24 24" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
      </svg>
      <p className="mt-4 text-sm text-white/60">Signing you in…</p>
    </div>
  );
}

// Modal popup for new OAuth users to complete their profile
function ProfileModal({ onDone }) {
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [picture, setPicture] = useState(null);
  const [cv, setCv] = useState(null);
  const [err, setErr] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const pictureInputRef = useRef(null);
  const cvInputRef = useRef(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setErr("");
    if (!picture || !cv) {
      setErr("Profile picture and CV are both required.");
      return;
    }
    setSubmitting(true);
    const fd = new FormData();
    fd.append("city", city);
    fd.append("country", country);
    fd.append("picture", picture);
    fd.append("cv", cv);
    try {
      await api.post("/applicant/complete-profile", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onDone();
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : "Something went wrong. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-6 backdrop-blur-sm">
      <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <div className="border-b border-slate-100 bg-primary px-6 py-5 text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/70">Complete your profile</p>
          <h2 className="mt-1 text-2xl font-bold leading-tight">Welcome to SeekJob</h2>
          <p className="mt-1.5 text-sm text-white/80">
            Add your profile details so employers can discover you and review your application.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 p-6">
          {err && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {err}
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              City
              <input
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="e.g. London"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Country
              <input
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="e.g. United Kingdom"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
              />
            </label>
          </div>

          <div className="space-y-3">
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-800">Profile photo</p>
                <span className="text-xs text-slate-500">JPG/JPEG, up to 5 MB</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-xs text-slate-600">{picture ? picture.name : "No file selected"}</p>
                <button
                  type="button"
                  className="shrink-0 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                  onClick={() => pictureInputRef.current?.click()}
                >
                  {picture ? "Change" : "Upload"}
                </button>
              </div>
              <input
                ref={pictureInputRef}
                type="file"
                accept=".jpg,.jpeg"
                className="sr-only"
                onChange={(e) => setPicture(e.target.files?.[0] || null)}
              />
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-800">CV / Resume</p>
                <span className="text-xs text-slate-500">PDF, up to 2 MB</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-xs text-slate-600">{cv ? cv.name : "No file selected"}</p>
                <button
                  type="button"
                  className="shrink-0 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                  onClick={() => cvInputRef.current?.click()}
                >
                  {cv ? "Change" : "Upload"}
                </button>
              </div>
              <input
                ref={cvInputRef}
                type="file"
                accept=".pdf"
                className="sr-only"
                onChange={(e) => setCv(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-white transition hover:bg-[#002a66] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Saving profile..." : "Save and continue"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [stage, setStage] = useState("loading"); // "loading" | "profile"

  useEffect(() => {
    const token = searchParams.get("token");
    const role = searchParams.get("role") || "applicant";
    const needsProfile = searchParams.get("needs_profile") === "true";
    const error = searchParams.get("error");

    if (error || !token) {
      navigate("/login/applicant?error=" + (error || "oauth_failed"), { replace: true });
      return;
    }

    login(token, role)
      .then(() => {
        if (needsProfile) {
          setStage("profile");
        } else {
          navigate("/jobs", { replace: true });
        }
      })
      .catch(() => {
        navigate("/login/applicant", { replace: true });
      });
  }, []);

  if (stage === "loading") return <LoadingScreen />;

  return <ProfileModal onDone={() => navigate("/jobs", { replace: true })} />;
}
