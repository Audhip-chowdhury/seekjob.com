import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";
import { useVisiblePolling } from "../hooks/useVisiblePolling";

export default function ApplicantDashboard() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const { role } = useAuth();

  const load = useCallback(() => {
    return api
      .get("/applicant/applications")
      .then((res) => setApps(res.data))
      .catch(() => setApps([]));
  }, []);

  useEffect(() => {
    if (role !== "applicant") return;
    setLoading(true);
    load().finally(() => setLoading(false));
  }, [role, load]);

  useVisiblePolling(() => {
    if (role !== "applicant") return;
    load();
  }, 4000);

  if (role !== "applicant") {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">
          <Link to="/login/applicant" className="text-primary underline">
            Sign in as an applicant
          </Link>{" "}
          to view your applications.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-3xl font-bold text-primary">My applications</h1>
        <p className="text-gray-600">History and status for every role you applied to</p>
        {loading ? (
          <p className="mt-8">Loading…</p>
        ) : (
          <div className="mt-6 overflow-x-auto rounded-lg border bg-white shadow">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface">
                <tr>
                  <th className="p-3">Role</th>
                  <th className="p-3">Company</th>
                  <th className="p-3">Applied</th>
                  <th className="p-3">Status</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {apps.map((a) => (
                  <tr key={a.id} className="border-t">
                    <td className="p-3 font-medium">{a.job_role}</td>
                    <td className="p-3">{a.company_name}</td>
                    <td className="p-3 text-gray-600">{new Date(a.applied_at).toLocaleString()}</td>
                    <td className="p-3">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="p-3">
                      <Link to={`/jobs/${a.job_id}`} className="text-primary hover:underline">
                        View job
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {apps.length === 0 && (
              <p className="p-6 text-center text-gray-500">No applications yet. Browse jobs to apply.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
