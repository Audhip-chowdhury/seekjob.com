import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import { useVisiblePolling } from "../hooks/useVisiblePolling";

export default function ApplicantOffers() {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { role } = useAuth();

  const load = useCallback(() => {
    return api.get("/applicant/offers").then((res) => setOffers(res.data));
  }, []);

  useEffect(() => {
    if (role !== "applicant") return;
    setLoading(true);
    load()
      .catch(() => setOffers([]))
      .finally(() => setLoading(false));
  }, [role, load]);

  useVisiblePolling(() => {
    if (role === "applicant") load().catch(() => {});
  }, 8000);

  if (role !== "applicant") {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">
          <Link to="/login/applicant" className="text-primary underline">
            Sign in as an applicant
          </Link>{" "}
          to view offer letters.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-3xl font-bold text-primary">Offer letters</h1>
        <p className="text-gray-600">Offers received from employers via your recruitment integration</p>
        {loading ? (
          <p className="mt-8">Loading…</p>
        ) : offers.length === 0 ? (
          <p className="mt-8 rounded-lg border border-gray-200 bg-white p-6 text-center text-gray-500 shadow-sm">
            No offer letters yet. When an employer sends an offer through HworkR, it will appear here.
          </p>
        ) : (
          <ul className="mt-6 space-y-4">
            {offers.map((o) => (
              <li key={o.id} className="rounded-lg border bg-white p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-ink">{o.job_role || "Role"}</p>
                    <p className="text-sm text-gray-600">{o.company_name || "Company"}</p>
                    <p className="mt-1 text-xs text-gray-500">
                      Status: <span className="font-medium text-gray-700">{o.external_offer_status}</span>
                      {o.sent_at && (
                        <>
                          {" "}
                          · Sent {new Date(o.sent_at).toLocaleString()}
                        </>
                      )}
                    </p>
                    {(o.recruitment_job_id || o.job_posting_code) && (
                      <p className="mt-1 font-mono text-xs text-gray-500">
                        Job ID: {o.recruitment_job_id || o.job_posting_code}
                      </p>
                    )}
                    {(o.external_userid || o.recruitment_external_applicant_id) && (
                      <p className="font-mono text-xs text-gray-500">
                        User ID: {o.external_userid || o.recruitment_external_applicant_id}
                      </p>
                    )}
                    {(o.offer_id || o.external_offer_id) && (
                      <p className="font-mono text-xs text-gray-500">
                        Offer ID: {o.offer_id || o.external_offer_id}
                      </p>
                    )}
                    {(o.company_id || o.external_company_id) && (
                      <p className="font-mono text-xs text-gray-500">
                        Company ID: {o.company_id || o.external_company_id}
                      </p>
                    )}
                    {(o.applicant_response_status === "accepted" ||
                      o.applicant_response_status === "declined") && (
                      <p className="mt-1 text-xs font-medium text-gray-700">
                        Your response:{" "}
                        <span className="text-ink">
                          {o.applicant_response_status === "accepted" ? "Accepted" : "Declined"}
                        </span>
                      </p>
                    )}
                  </div>
                  <Link
                    to={`/applicant/offers/${o.id}`}
                    className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-[#002a66]"
                  >
                    View letter
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
