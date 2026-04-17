const styles = {
  Applied: "bg-blue-100 text-blue-800",
  Interview: "bg-amber-100 text-amber-900",
  Accepted: "bg-green-100 text-green-800",
  Rejected: "bg-red-100 text-red-800",
};

export default function StatusBadge({ status }) {
  const c = styles[status] || "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${c}`}>
      {status}
    </span>
  );
}
