import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { mediaUrl } from "../api";
import { useAuth } from "../context/AuthContext";

function initialsFromName(name) {
  if (!name || !name.trim()) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

function ProfileChip({ user, role }) {
  const [imgFailed, setImgFailed] = useState(false);
  const imagePath = role === "applicant" ? user?.picture_path : user?.logo_path;
  const src = imagePath ? mediaUrl(imagePath) : null;
  const showImg = src && !imgFailed;

  return (
    <div className="flex items-center gap-2 rounded-lg border border-white/40 bg-white/15 px-2.5 py-1.5 shadow-inner">
      {showImg ? (
        <img
          src={src}
          alt=""
          className="h-9 w-9 shrink-0 rounded-md border border-white/30 object-cover"
          onError={() => setImgFailed(true)}
        />
      ) : (
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-white/30 bg-white/20 text-xs font-bold text-white"
          aria-hidden
        >
          {initialsFromName(user?.name)}
        </div>
      )}
      <div className="min-w-0 text-left leading-tight">
        <p className="max-w-[10rem] truncate text-xs font-semibold text-white">{user?.name}</p>
        <p className="text-[10px] font-medium uppercase tracking-wide text-white/70">
          {role === "company" ? "Company" : "Applicant"}
        </p>
      </div>
    </div>
  );
}

export default function Navbar() {
  const { role, user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="bg-primary text-white shadow-md">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3">
        <Link to="/" className="text-xl font-bold tracking-tight">
          SeekJob<span className="text-accent">.</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-4 text-sm font-medium">
          <Link to="/jobs" className="hover:text-accent">
            Jobs
          </Link>
          <Link to="/discussions" className="hover:text-accent">
            Discussions
          </Link>
          {role === "applicant" && (
            <>
              <Link to="/applicant/applications" className="hover:text-accent">
                My applications
              </Link>
              <Link to="/applicant/offers" className="hover:text-accent">
                Offer letters
              </Link>
              {user && <ProfileChip user={user} role="applicant" />}
            </>
          )}
          {role === "company" && (
            <>
              <Link to="/company/create-job" className="hover:text-accent">
                Create postings
              </Link>
              <Link to="/company/applications" className="hover:text-accent">
                Applicants
              </Link>
              {user && <ProfileChip user={user} role="company" />}
            </>
          )}
          {!role && (
            <>
              <Link to="/login/applicant" className="hover:text-accent">
                Applicant login
              </Link>
              <Link to="/login/company" className="hover:text-accent">
                Company login
              </Link>
            </>
          )}
          {role && (
            <button
              type="button"
              className="rounded bg-white/10 px-3 py-1 hover:bg-white/20"
              onClick={() => {
                logout();
                navigate("/");
              }}
            >
              Log out
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
