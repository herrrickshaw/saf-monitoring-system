import { useEffect, useState } from "react";
import { fetchBlendingCompliance } from "../api/client";
import DataTable from "../components/DataTable";

export default function BlendingCompliance() {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    fetchBlendingCompliance().then(setRecords);
  }, []);

  const columns = [
    { key: "airport", label: "Airport" },
    { key: "year", label: "Year" },
    { key: "total_jet_fuel_liters", label: "Total Jet Fuel (L)", render: (r) => r.total_jet_fuel_liters.toLocaleString() },
    { key: "total_saf_liters", label: "Total SAF Blended (L)", render: (r) => r.total_saf_liters.toLocaleString() },
    { key: "actual_pct", label: "Actual %", render: (r) => `${r.actual_pct}%` },
    { key: "mandate_pct", label: "ReFuelEU Mandate %", render: (r) => `${r.mandate_pct}%` },
    {
      key: "compliant",
      label: "Status",
      render: (r) => (
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${r.compliant ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
          {r.compliant ? "Compliant" : "Below Mandate"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Blending Target Compliance</h2>
      <DataTable columns={columns} rows={records} emptyMessage="No blending records yet." />
    </div>
  );
}
