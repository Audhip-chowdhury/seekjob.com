import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, mediaUrl } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";

const STATUSES = ["Applied", "Interview", "Accepted", "Rejected"];

export default function CompanyApplications() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(null);
  const { role } = useAuth();

  function load() {
    return api.get("/company/applications").then((res) => setApps(res.data));
  }

  useEffect(() => {
    if (role !== "company") return;
    load()
      .catch(() => setApps([]))
      .finally(() => setLoading(false));
  }, [role]);

  async function setStatus(id, status) {
    setUpdating(id);
    try {
      await api.patch(`/applications/${id}/status`, { status });
      await load();
    } catch {
      /* ignore */
    } finally {
      setUpdating(null);
    }
  }

  if (role !== "company") {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">
          <Link to="/login/company" className="text-primary underline">
            Sign in as a company
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-3xl font-bold text-primary">Applicants</h1>
        <p className="text-gray-600">Everyone who applied to your postings</p>
        {loading ? (
          <p className="mt-8">Loading…</p>
        ) : (
          <div className="mt-6 overflow-x-auto rounded-lg border bg-white shadow">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface">
                <tr>
                  <th className="p-3">Applicant</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Applied</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Photo / CV</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((a) => (
                  <tr key={a.id} className="border-t">
                    <td className="p-3 font-medium">{a.applicant_name}</td>
                    <td className="p-3">
                      <a href={`mailto:${a.applicant_email}`} className="text-primary hover:underline">
                        {a.applicant_email}
                      </a>
                    </td>
                    <td className="p-3">{a.job_role}</td>
                    <td className="p-3 text-gray-600">{new Date(a.applied_at).toLocaleString()}</td>
                    <td className="p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge status={a.status} />
                        <select
                          className="rounded border px-2 py-1 text-xs"
                          value={a.status}
                          disabled={updating === a.id}
                          onChange={(e) => setStatus(a.id, e.target.value)}
                        >
                          {STATUSES.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-col gap-1 text-xs">
                        {a.applicant_picture_path && (
                          <a
                            href={mediaUrl(a.applicant_picture_path)}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary hover:underline"
                          >
                            Photo
                          </a>
                        )}
                        {a.applicant_cv_path && (
                          <a
                            href={mediaUrl(a.applicant_cv_path)}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary hover:underline"
                          >
                            CV (PDF)
                          </a>
                        )}
                        <Link to={`/jobs/${a.job_id}`} className="text-gray-600 hover:underline">
                          View job
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {apps.length === 0 && (
              <p className="p-6 text-center text-gray-500">No applications yet.</p>
            )}
          </div>
        )}
        <p className="mt-4 text-xs text-gray-500">
          Full profile assets (photo & CV) are stored securely; contact applicants via email for next steps.
        </p>
      </div>
    </div>
  );
}
