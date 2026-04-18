/**
 * Renders HworkR ``compensation_json.offer_letter`` (schema_version 1) defensively.
 */
function Section({ title, children }) {
  if (!children) return null;
  return (
    <section className="mt-6">
      <h3 className="border-b border-gray-200 pb-1 text-sm font-semibold uppercase tracking-wide text-primary">{title}</h3>
      <div className="mt-3 space-y-2 text-sm text-gray-800">{children}</div>
    </section>
  );
}

function Field({ label, value }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <p>
      <span className="font-medium text-gray-700">{label}: </span>
      <span className="whitespace-pre-wrap">{typeof value === "boolean" ? (value ? "Yes" : "No") : String(value)}</span>
    </p>
  );
}

export default function OfferLetterView({ compensationJson }) {
  const root = compensationJson && typeof compensationJson === "object" ? compensationJson : {};
  const nested = root.offer_letter;
  const letter =
    nested && typeof nested === "object" && Object.keys(nested).length > 0
      ? nested
      : root.candidate || root.role || root.compensation || root.joining
        ? root
        : {};
  const candidate = letter.candidate || {};
  const role = letter.role || {};
  const compensation = letter.compensation || {};
  const joining = letter.joining || {};
  const compliance = letter.compliance || {};
  const signoff = letter.signoff || {};
  const prefill = root.prefill || {};

  const hasLetter = Object.keys(letter).length > 0;

  if (!hasLetter) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p className="font-medium">Structured offer letter</p>
        <p className="mt-1 text-amber-800">
          This payload has no <code className="rounded bg-amber-100 px-1">offer_letter</code> block yet, or uses a newer
          schema. Raw keys: {Object.keys(root).length ? Object.keys(root).join(", ") : "none"}.
        </p>
        {Object.keys(root).length > 0 && (
          <pre className="mt-3 max-h-48 overflow-auto rounded bg-white/80 p-2 text-xs text-gray-700">{JSON.stringify(root, null, 2)}</pre>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2 text-gray-900">
      {root.schema_version != null && (
        <p className="text-xs text-gray-500">
          Schema version <span className="font-mono">{String(root.schema_version)}</span>
        </p>
      )}

      <Section title="Candidate">
        <Field label="Full name" value={candidate.full_name} />
        <Field label="Letter date" value={candidate.letter_date} />
        <Field label="Address / email" value={candidate.address_or_email} />
      </Section>

      <Section title="Role">
        <Field label="Job title" value={role.job_title} />
        <Field label="Department" value={role.department_name || role.department_id} />
        <Field label="Reporting manager" value={role.reporting_manager_name || role.reporting_manager_employee_id} />
        <Field label="Employment type" value={role.employment_type} />
        <Field label="Work location" value={role.work_location_mode} />
      </Section>

      <Section title="Compensation">
        <Field label="Annual CTC" value={compensation.annual_ctc} />
        <Field label="Fixed / variable split" value={compensation.fixed_variable_split} />
        <Field label="Pay frequency" value={compensation.pay_frequency} />
        <Field label="Bonus / incentive" value={compensation.bonus_incentive} />
        <Field label="Stock / ESOP" value={compensation.stock_esop} />
      </Section>

      <Section title="Joining">
        <Field label="Date of joining" value={joining.date_of_joining} />
        <Field label="Offer expiry" value={joining.offer_expiry} />
        <Field label="Probation" value={joining.probation} />
        <Field label="Notice period" value={joining.notice_period} />
      </Section>

      <Section title="Compliance">
        <Field label="Background verification" value={compliance.background_verification} />
        <Field label="Confidentiality / NDA" value={compliance.confidentiality_nda} />
        <Field label="Non-compete" value={compliance.non_compete} />
        <Field label="Documents on joining" value={compliance.documents_on_joining} />
      </Section>

      <Section title="Sign-off">
        <Field label="Company" value={signoff.company_name} />
        <Field label="Include logo / seal" value={signoff.include_logo_seal} />
        <Field label="Candidate signature line" value={signoff.candidate_signature_line} />
      </Section>

      {(prefill.application_id || prefill.job_grade) && (
        <section className="mt-6 rounded-lg bg-gray-50 p-3 text-xs text-gray-600">
          <p className="font-semibold text-gray-700">Prefill</p>
          <Field label="Application id" value={prefill.application_id} />
          <Field label="Job grade" value={prefill.job_grade} />
        </section>
      )}
    </div>
  );
}
