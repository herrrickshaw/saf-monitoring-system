import { useState } from "react";
import AirlineReporting from "./pages/AirlineReporting";
import BlendingCompliance from "./pages/BlendingCompliance";
import CarbonCredits from "./pages/CarbonCredits";
import Certificates from "./pages/Certificates";
import Dashboard from "./pages/Dashboard";
import FeedstockArrivals from "./pages/FeedstockArrivals";
import IndiaCCTS from "./pages/IndiaCCTS";
import ProductionBatches from "./pages/ProductionBatches";

const VIEWS = [
  { key: "dashboard", label: "Dashboard", component: Dashboard },
  { key: "feedstock", label: "Feedstock Arrivals", component: FeedstockArrivals },
  { key: "production", label: "Production Batches", component: ProductionBatches },
  { key: "certificates", label: "Certificates", component: Certificates },
  { key: "credits", label: "Carbon Credits", component: CarbonCredits },
  { key: "airlines", label: "Airline Reporting", component: AirlineReporting },
  { key: "blending", label: "Blending Compliance", component: BlendingCompliance },
  { key: "ccts", label: "India CCTS/ICM", component: IndiaCCTS },
];

export default function App() {
  const [active, setActive] = useState("dashboard");
  const ActiveComponent = VIEWS.find((v) => v.key === active)?.component ?? Dashboard;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-3">
          <h1 className="text-xl font-bold text-slate-900">SAF Monitoring System</h1>
          <nav className="mt-3 flex flex-wrap gap-1">
            {VIEWS.map((v) => (
              <button
                key={v.key}
                onClick={() => setActive(v.key)}
                className={`rounded px-3 py-1.5 text-sm font-medium ${
                  active === v.key ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {v.label}
              </button>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <ActiveComponent />
      </main>
    </div>
  );
}
