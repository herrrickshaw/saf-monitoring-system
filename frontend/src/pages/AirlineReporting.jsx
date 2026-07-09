import { useEffect, useState } from "react";
import { airlineReportUrl, fetchAirlines } from "../api/client";

export default function AirlineReporting() {
  const [airlines, setAirlines] = useState([]);
  const [offtakeId, setOfftakeId] = useState("");
  const [start, setStart] = useState("2025-01-01");
  const [end, setEnd] = useState(new Date().toISOString().slice(0, 10));
  const [fmt, setFmt] = useState("pdf");

  useEffect(() => {
    fetchAirlines().then((data) => {
      setAirlines(data);
      if (data.length) setOfftakeId(String(data[0].id));
    });
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Airline Reporting</h2>
      <div className="max-w-xl space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <label className="block text-sm">
          Airline
          <select
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
            value={offtakeId}
            onChange={(e) => setOfftakeId(e.target.value)}
          >
            {airlines.map((a) => (
              <option key={a.id} value={a.id}>
                {a.airline_name} ({a.delivery_airport})
              </option>
            ))}
          </select>
        </label>

        <div className="flex gap-3">
          <label className="block flex-1 text-sm">
            Start
            <input
              type="date"
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label className="block flex-1 text-sm">
            End
            <input
              type="date"
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </label>
        </div>

        <label className="block text-sm">
          Format
          <select className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5" value={fmt} onChange={(e) => setFmt(e.target.value)}>
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
          </select>
        </label>

        <a
          href={offtakeId ? airlineReportUrl(offtakeId, start, end, fmt) : "#"}
          className={`inline-block rounded px-4 py-2 text-sm font-medium text-white ${offtakeId ? "bg-slate-900 hover:bg-slate-700" : "pointer-events-none bg-slate-300"}`}
        >
          Download Traceable Report
        </a>
      </div>
    </div>
  );
}
