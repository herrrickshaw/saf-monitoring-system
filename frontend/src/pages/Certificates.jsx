import { useEffect, useState } from "react";
import { fetchCertificates, fetchProductionBatches } from "../api/client";
import DataTable from "../components/DataTable";

export default function Certificates() {
  const [certificates, setCertificates] = useState([]);
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    fetchCertificates().then(setCertificates);
    fetchProductionBatches().then(setBatches);
  }, []);

  const batchCode = (id) => batches.find((b) => b.id === id)?.batch_code ?? id;

  const flag = (ok) => (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${ok ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
      {ok ? "Yes" : "No"}
    </span>
  );

  const columns = [
    { key: "production_batch_id", label: "Batch", render: (r) => batchCode(r.production_batch_id) },
    { key: "ghg_intensity", label: "RED III GHG Intensity (gCO2eq/MJ)", render: (r) => r.ghg_intensity.toFixed(2) },
    { key: "ghg_savings_pct", label: "RED III GHG Savings %", render: (r) => `${r.ghg_savings_pct}%` },
    { key: "corsia_lcef", label: "CORSIA L_CEF (gCO2e/MJ)", render: (r) => r.corsia_lcef.toFixed(2) },
    { key: "corsia_reduction_pct", label: "CORSIA Reduction %", render: (r) => `${r.corsia_reduction_pct}%` },
    { key: "eligible_feedstock", label: "RED Eligible Feedstock", render: (r) => flag(r.eligible_feedstock) },
    { key: "astm_conformant", label: "ASTM D7566 Conformant", render: (r) => flag(r.astm_conformant) },
    { key: "corsia_eligible", label: "CORSIA Eligible (≥10%)", render: (r) => flag(r.corsia_eligible) },
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">SAF Certificates</h2>
      <DataTable columns={columns} rows={certificates} emptyMessage="No certificates generated yet." />
    </div>
  );
}
