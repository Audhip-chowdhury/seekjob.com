import { useEffect, useState } from "react";
import { api } from "../api";
import Navbar from "../components/Navbar";
import JobCard from "../components/JobCard";
import FilterBar from "../components/FilterBar";

export default function JobList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [company, setCompany] = useState("");
  const [jobType, setJobType] = useState("");
  const [sortBy, setSortBy] = useState("date_desc");
  const [debouncedCompany, setDebouncedCompany] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebouncedCompany(company), 400);
    return () => clearTimeout(t);
  }, [company]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params = { sort_by: sortBy };
    if (debouncedCompany.trim()) params.company = debouncedCompany.trim();
    if (jobType) params.job_type = jobType;
    api
      .get("/jobs", { params })
      .then((res) => {
        if (!cancelled) setItems(res.data.items || []);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedCompany, jobType, sortBy]);

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-3xl font-bold text-primary">Job openings</h1>
        <p className="mt-1 text-gray-600">Browse all open roles</p>
        <div className="mt-6">
          <FilterBar
            company={company}
            setCompany={setCompany}
            jobType={jobType}
            setJobType={setJobType}
            sortBy={sortBy}
            setSortBy={setSortBy}
          />
        </div>
        {loading ? (
          <p className="mt-8 text-center text-gray-500">Loading…</p>
        ) : (
          <ul className="mt-6 space-y-4">
            {items.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </ul>
        )}
        {!loading && items.length === 0 && (
          <p className="mt-8 text-center text-gray-500">No jobs match your filters.</p>
        )}
      </div>
    </div>
  );
}
