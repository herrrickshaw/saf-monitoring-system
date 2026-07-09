import { useEffect, useState } from "react";
import { fetchAirlineDeliveries, fetchCarbonCreditLedger } from "../api/client";
import DataTable from "../components/DataTable";

export default function CarbonCredits() {
  const [ledger, setLedger] = useState([]);
  const [deliveries, setDeliveries] = useState([]);

  useEffect(() => {
    fetchCarbonCreditLedger().then(setLedger);
    fetchAirlineDeliveries().then(setDeliveries);
  }, []);

  const deliveryVolume = (id) => {
    const d = deliveries.find((d) => d.id === id);
    return d ? `${d.volume_liters.toLocaleString()} L` : id;
  };

  const columns = [
    { key: "airline_delivery_id", label: "Airline Delivery", render: (r) => deliveryVolume(r.airline_delivery_id) },
    { key: "tco2e_saved", label: "tCO2e Saved", render: (r) => r.tco2e_saved.toLocaleString() },
    {
      key: "status",
      label: "Status",
      render: (r) => (
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${r.status === "reported" ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-600"}`}>
          {r.status}
        </span>
      ),
    },
    { key: "calculated_date", label: "Calculated" },
  ];

  const total = ledger.reduce((sum, l) => sum + l.tco2e_saved, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Carbon Credit Ledger (CORSIA)</h2>
        <div className="text-sm text-slate-500">Total: {total.toLocaleString(undefined, { maximumFractionDigits: 1 })} tCO2e</div>
      </div>
      <DataTable columns={columns} rows={ledger} emptyMessage="No carbon credit entries yet." />
    </div>
  );
}
