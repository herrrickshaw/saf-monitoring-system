import { useEffect, useState } from "react";
import { fetchASTMPathways, fetchProductionBatches } from "../api/client";
import DataTable from "../components/DataTable";

export default function ProductionBatches() {
  const [batches, setBatches] = useState([]);
  const [pathways, setPathways] = useState([]);

  useEffect(() => {
    fetchProductionBatches().then(setBatches);
    fetchASTMPathways().then(setPathways);
  }, []);

  const pathwayCode = (id) => pathways.find((p) => p.id === id)?.code ?? id;

  const columns = [
    { key: "batch_code", label: "Batch Code" },
    { key: "start_date", label: "Start" },
    { key: "end_date", label: "End" },
    { key: "astm_pathway_id", label: "ASTM Pathway", render: (r) => pathwayCode(r.astm_pathway_id) },
    { key: "feedstock_input_tonnes", label: "Feedstock In (t)" },
    { key: "saf_output_liters", label: "SAF Out (L)", render: (r) => r.saf_output_liters.toLocaleString() },
    { key: "yield_pct", label: "Yield %" },
    { key: "blend_ratio_pct", label: "Blend Ratio %" },
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Production Batches</h2>
      <DataTable columns={columns} rows={batches} emptyMessage="No production batches recorded yet." />
    </div>
  );
}
