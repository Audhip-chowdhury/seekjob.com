import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import OfferLetterView from "../components/OfferLetterView";
import OfferResponseActions from "../components/OfferResponseActions";

export default function ApplicantOfferDetail() {
  const { offerId } = useParams();
  const [offer, setOffer] = useState(null);
  const [err, setErr] = useState("");
  const { role } = useAuth();

  useEffect(() => {
    if (role !== "applicant" || !offerId) return;
    api
      .get(`/applicant/offers/${offerId}`)
      .then((res) => setOffer(res.data))
      .catch(() => setErr("Offer not found or you do not have access."));
  }, [role, offerId]);

  if (role !== "applicant") {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">
          <Link to="/login/applicant" className="text-primary underline">
            Sign in as an applicant
          </Link>
        </p>
      </div>
    );
  }

  if (err || !offer) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">{err || "Loading…"}</p>
        <p className="text-center">
          <Link to="/applicant/offers" className="text-primary underline">
            Back to offers
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <article className="mx-auto max-w-3xl px-4 py-8">
        <Link to="/applicant/offers" className="text-sm font-medium text-primary hover:underline">
          ← All offers
        </Link>
        <header className="mt-4 border-b border-gray-200 pb-4">
          <h1 className="text-2xl font-bold text-primary">{offer.job_role || "Offer letter"}</h1>
          <p className="text-gray-700">{offer.company_name}</p>
          <p className="mt-2 text-sm text-gray-600">
            Status <span className="font-medium text-ink">{offer.external_offer_status}</span>
            {offer.start_date && (
              <>
                {" "}
                · Start {offer.start_date}
              </>
            )}
            {offer.sent_at && (
              <>
                {" "}
                · Sent {new Date(offer.sent_at).toLocaleString()}
              </>
            )}
          </p>
          {(offer.recruitment_job_id || offer.job_posting_code) && (
            <p className="mt-1 font-mono text-xs text-gray-500">
              Recruitment job ID: {offer.recruitment_job_id || offer.job_posting_code}
            </p>
          )}
          {(offer.external_userid || offer.recruitment_external_applicant_id) && (
            <p className="mt-1 font-mono text-xs text-gray-500">
              External user ID: {offer.external_userid || offer.recruitment_external_applicant_id}
            </p>
          )}
          {(offer.offer_id || offer.external_offer_id) && (
            <p className="mt-1 font-mono text-xs text-gray-500">
              Offer ID: {offer.offer_id || offer.external_offer_id}
            </p>
          )}
          {(offer.company_id || offer.external_company_id) && (
            <p className="mt-1 font-mono text-xs text-gray-500">
              Company ID: {offer.company_id || offer.external_company_id}
            </p>
          )}
        </header>
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <OfferLetterView compensationJson={offer.compensation_json} />
          <OfferResponseActions offer={offer} onOfferUpdated={setOffer} />
        </div>
      </article>
    </div>
  );
}
