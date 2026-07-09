import { useEffect, useState } from "react";
import { fetchBioCarbonTable } from "../api/client";

export default function BioCarbonEstimator() {
  const [table, setTable] = useState(null);
  const [capacities, setCapacities] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBioCarbonTable()
      .then((data) => {
        setTable(data);
        const initial = {};
        data.rows.forEach((r) => {
          initial[r.key] = r.reference_capacity_tpd;
        });
        setCapacities(initial);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="text-rose-600">Failed to load: {error}</div>;
  if (!table) return <div className="text-slate-400">Loading...</div>;

  const creditFor = (row) => {
    const capacity = parseFloat(capacities[row.key]);
    if (Number.isNaN(capacity)) return 0;
    return Math.round(capacity * table.operating_days_per_year * row.credit_factor_tco2e_per_tonne * 10) / 10;
  };

  const totalCredit = table.rows.reduce((sum, r) => sum + creditFor(r), 0);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Bio-Carbon Credit Estimator</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">
          Modeled on the UPNEDA Bio Carbon Credit Calculator (feedstock type + daily plant capacity in
          TPD &rarr; estimated annual credits). {table.note}
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-slate-500">Feedstock</th>
              <th className="px-4 py-2 text-left font-medium text-slate-500">Capacity (TPD)</th>
              <th className="px-4 py-2 text-left font-medium text-slate-500">Illustrative Factor (tCO2e/tonne)</th>
              <th className="px-4 py-2 text-left font-medium text-slate-500">Est. Credit/Year (tCO2e)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {table.rows.map((row) => (
              <tr key={row.key} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-2 text-slate-700">{row.label}</td>
                <td className="whitespace-nowrap px-4 py-2">
                  <input
                    type="number"
                    min="0"
                    step="any"
                    className="w-28 rounded border border-slate-300 px-2 py-1"
                    value={capacities[row.key] ?? ""}
                    onChange={(e) => setCapacities({ ...capacities, [row.key]: e.target.value })}
                  />
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-slate-500">{row.credit_factor_tco2e_per_tonne}</td>
                <td className="whitespace-nowrap px-4 py-2 font-medium text-slate-900">
                  {creditFor(row).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-slate-200 bg-slate-50">
              <td className="px-4 py-2 font-semibold text-slate-700" colSpan={3}>
                Total
              </td>
              <td className="px-4 py-2 font-semibold text-slate-900">
                {totalCredit.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
