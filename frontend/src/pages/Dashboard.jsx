import { useEffect, useState } from "react";
import { fetchDashboardSummary } from "../api/client";
import KpiCard from "../components/KpiCard";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardSummary().then(setSummary).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="text-rose-600">Failed to load dashboard: {error}</div>;
  if (!summary) return <div className="text-slate-400">Loading...</div>;

  const blendingCompliant = summary.current_year_blending_pct >= summary.current_year_mandate_pct;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        label="Total SAF Produced"
        value={`${(summary.total_saf_liters / 1_000_000).toFixed(2)}M L`}
      />
      <KpiCard
        label="tCO2e Credited (CORSIA)"
        value={summary.total_tco2e_credited.toLocaleString(undefined, { maximumFractionDigits: 1 })}
      />
      <KpiCard label="Active Airline Contracts" value={summary.active_contracts} />
      <KpiCard
        label="Blending vs Mandate (this year)"
        value={`${summary.current_year_blending_pct}% / ${summary.current_year_mandate_pct}%`}
        tone={blendingCompliant ? "good" : "bad"}
        sublabel={blendingCompliant ? "On track" : "Below ReFuelEU mandate"}
      />
    </div>
  );
}
