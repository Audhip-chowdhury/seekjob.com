const JOB_TYPES = ["", "Management", "HR", "Software Dev", "Ops"];

export default function FilterBar({
  company,
  setCompany,
  jobType,
  setJobType,
  sortBy,
  setSortBy,
}) {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm md:flex-row md:flex-wrap md:items-end">
      <label className="flex flex-1 flex-col gap-1 text-sm">
        <span className="font-medium text-gray-700">Company name</span>
        <input
          type="search"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Filter by company"
          className="rounded border border-gray-300 px-3 py-2"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-gray-700">Job type</span>
        <select
          value={jobType}
          onChange={(e) => setJobType(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        >
          {JOB_TYPES.map((t) => (
            <option key={t || "all"} value={t}>
              {t || "All types"}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-gray-700">Sort by date</span>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        >
          <option value="date_desc">Newest first</option>
          <option value="date_asc">Oldest first</option>
        </select>
      </label>
    </div>
  );
}
