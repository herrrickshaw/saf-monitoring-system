import { useEffect, useState } from "react";
import { estimateCCTS, fetchCCTSStatus } from "../api/client";
import KpiCard from "../components/KpiCard";

export default function IndiaCCTS() {
  const [status, setStatus] = useState(null);
  const [form, setForm] = useState({ actual_intensity_tco2e_per_unit: "", target_intensity_tco2e_per_unit: "", output_units: "" });
  const [estimate, setEstimate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCCTSStatus().then(setStatus).catch((e) => setError(e.message));
  }, []);

  const handleEstimate = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const result = await estimateCCTS({
        actual_intensity_tco2e_per_unit: parseFloat(form.actual_intensity_tco2e_per_unit),
        target_intensity_tco2e_per_unit: parseFloat(form.target_intensity_tco2e_per_unit),
        output_units: parseFloat(form.output_units),
      });
      setEstimate(result);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!status) return <div className="text-slate-400">Loading...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">India Carbon Credit Trading Scheme (CCTS / ICM)</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">
          Bureau of Energy Efficiency's domestic carbon market. SAF/aviation fuel production is not a
          notified sector under either mechanism yet -- this section tracks coverage status and lets you
          run what-if Carbon Credit Certificate (CCC) estimates once BEE publishes a target.
        </p>
      </div>

      <KpiCard
        label="SAF/Aviation Notified Under CCTS?"
        value={status.saf_sector_notified ? "Yes" : "Not Yet"}
        tone={status.saf_sector_notified ? "good" : "default"}
        sublabel={status.note}
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700">Compliance Mechanism Sectors</h3>
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {status.compliance_mechanism_sectors.map((s) => (
              <li key={s} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                {s}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700">Offset Mechanism Sectors</h3>
          <div className="mt-2 space-y-2">
            <div>
              <div className="text-xs font-medium text-slate-400">Phase I</div>
              <ul className="mt-1 flex flex-wrap gap-1.5">
                {status.offset_mechanism_phase_1_sectors.map((s) => (
                  <li key={s} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-xs font-medium text-slate-400">Phase II</div>
              <ul className="mt-1 flex flex-wrap gap-1.5">
                {status.offset_mechanism_phase_2_sectors.map((s) => (
                  <li key={s} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-700">Governing Bodies</h3>
        <dl className="mt-2 space-y-1 text-sm">
          {Object.entries(status.governing_bodies).map(([name, role]) => (
            <div key={name} className="flex gap-2">
              <dt className="font-medium text-slate-600">{name}:</dt>
              <dd className="text-slate-500">{role}</dd>
            </div>
          ))}
        </dl>
      </div>

      <form onSubmit={handleEstimate} className="max-w-xl space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-700">What-If CCC Surplus/Deficit Estimator</h3>
        <label className="block text-sm">
          Actual GHG Intensity (tCO2e / unit output)
          <input
            type="number"
            step="any"
            required
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
            value={form.actual_intensity_tco2e_per_unit}
            onChange={(e) => setForm({ ...form, actual_intensity_tco2e_per_unit: e.target.value })}
          />
        </label>
        <label className="block text-sm">
          Target GHG Intensity (tCO2e / unit output)
          <input
            type="number"
            step="any"
            required
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
            value={form.target_intensity_tco2e_per_unit}
            onChange={(e) => setForm({ ...form, target_intensity_tco2e_per_unit: e.target.value })}
          />
        </label>
        <label className="block text-sm">
          Output (units of product for the period)
          <input
            type="number"
            step="any"
            required
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
            value={form.output_units}
            onChange={(e) => setForm({ ...form, output_units: e.target.value })}
          />
        </label>
        <button type="submit" className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
          Estimate
        </button>

        {error && <div className="text-sm text-rose-600">{error}</div>}
        {estimate && (
          <div className={`rounded p-3 text-sm ${estimate.is_surplus ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
            <div className="font-medium">
              {estimate.is_surplus ? "Surplus" : "Deficit"}: {estimate.ccc_equivalent.toLocaleString()} CCCs
              ({estimate.surplus_deficit_tco2e.toLocaleString()} tCO2e)
            </div>
            <div className="mt-1 text-xs opacity-80">{estimate.note}</div>
          </div>
        )}
      </form>
    </div>
  );
}
