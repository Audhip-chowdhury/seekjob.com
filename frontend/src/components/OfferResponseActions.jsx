import { useState } from "react";
import { api } from "../api";

function formatApiError(err) {
  const d = err.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join("; ");
  if (d && typeof d === "object") return JSON.stringify(d);
  return err.message || "Request failed";
}

/**
 * Two-step confirmation before PATCH /applicant/offers/:id/respond (accepted | declined).
 */
export default function OfferResponseActions({ offer, onOfferUpdated }) {
  const [dialog, setDialog] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const responded =
    offer?.applicant_response_status === "accepted" ||
    offer?.applicant_response_status === "declined";

  async function submit(status) {
    setSubmitting(true);
    setError("");
    try {
      await api.patch(`/applicant/offers/${offer.id}/respond`, { status });
      const refreshed = await api.get(`/applicant/offers/${offer.id}`);
      onOfferUpdated(refreshed.data);
      setDialog(null);
    } catch (e) {
      setError(formatApiError(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (responded) {
    const label =
      offer.applicant_response_status === "accepted" ? "Accepted" : "Declined";
    return (
      <div className="mt-6 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800">
        <span className="font-semibold text-ink">Your response:</span> {label}
        {offer.applicant_responded_at && (
          <span className="text-gray-600">
            {" "}
            · {new Date(offer.applicant_responded_at).toLocaleString()}
          </span>
        )}
      </div>
    );
  }

  const isAccept = dialog?.startsWith("accept");
  const step = dialog?.endsWith("1") ? 1 : 2;
  const verb = isAccept ? "accept" : "reject";
  const showModal = dialog != null;

  return (
    <div className="mt-8 border-t border-gray-200 pt-6">
      <p className="text-sm font-medium text-gray-800">Respond to this offer</p>
      <p className="mt-1 text-xs text-gray-500">
        You will be asked to confirm twice before your choice is sent.
      </p>
      {error && (
        <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={submitting}
          onClick={() => {
            setError("");
            setDialog("accept-1");
          }}
          className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#002a66] disabled:opacity-50"
        >
          Accept offer
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={() => {
            setError("");
            setDialog("reject-1");
          }}
          className="rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-semibold text-gray-800 hover:bg-gray-50 disabled:opacity-50"
        >
          Reject offer
        </button>
      </div>

      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="offer-respond-title"
        >
          <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-lg">
            <h2 id="offer-respond-title" className="text-lg font-semibold text-ink">
              {step === 1 ? "Please confirm" : "Confirm again"}
            </h2>
            <p className="mt-3 text-sm text-gray-700">
              {step === 1
                ? `Are you sure you want to ${verb} the offer?`
                : `Please confirm again: are you sure you want to ${verb} the offer?`}
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                disabled={submitting}
                onClick={() => setDialog(null)}
                className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              {step === 1 ? (
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => setDialog(isAccept ? "accept-2" : "reject-2")}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-[#002a66] disabled:opacity-50"
                >
                  Continue
                </button>
              ) : (
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => submit(isAccept ? "accepted" : "declined")}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 ${
                    isAccept ? "bg-primary hover:bg-[#002a66]" : "bg-red-700 hover:bg-red-800"
                  }`}
                >
                  {submitting ? "Sending…" : isAccept ? "Yes, accept" : "Yes, reject"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
