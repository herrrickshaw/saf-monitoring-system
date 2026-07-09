# SAF Monitoring System

A compliance monitoring platform for Sustainable Aviation Fuel (SAF) plant and supply-chain
operations: feedstock arrival tracking, production batch linkage, GHG intensity calculation,
ASTM D7566 pathway conformance, ReFuelEU Aviation blending-mandate compliance, CORSIA carbon
credit ledgering, and traceable airline reporting.

## Regulatory Disclaimer

This system implements the following regulatory frameworks as **editable defaults**, not
hardcoded truth. EU/EASA blending mandates, RED III default GHG values, and ASTM D7566
approved pathways/blend limits are periodically revised. **Confirm current values against
the official Delegated/Implementing Regulations, the current ASTM D7566 edition, and ICAO
CORSIA rules before using this system for real compliance reporting.**

- `backend/app/calculations/ghg.py` — RED III / EASA GHG intensity methodology
  (Annex V/VI-style formula) and fossil fuel comparator (94 gCO2eq/MJ)
- `backend/app/calculations/mandate_schedule.py` — ReFuelEU Aviation minimum SAF blending
  share by year
- `backend/app/calculations/astm_pathways.py` — ASTM D7566 approved conversion pathways and
  their certified max blend ratios
- `backend/app/calculations/corsia.py` — CORSIA eligibility threshold and tCO2e credit
  conversion

## Architecture

```
backend/   FastAPI app (SQLite via SQLAlchemy), flat routers/, mock data seeder
frontend/  React + Vite + Tailwind, single-page tab navigation
```

See `backend/app/models.py` for the full data model: feedstocks, deliveries, production
batches, ASTM pathways, SAF certificates, airline offtakes/deliveries, the carbon credit
ledger, and blending compliance records.

## Running Locally

Requires **Python 3.10+** (uses `X | None` type hints) and **Node 18+**.

```bash
./run_app.sh
```

This installs dependencies, starts the backend on `:8000` (Swagger docs at
`http://localhost:8000/docs`) and the frontend on `:5173`. On first run, the backend seeds
~12 months of realistic mock data (3 feedstocks, 36 production batches + certificates, 3
airline offtake contracts, a CORSIA credit ledger, and blending records for 3 airports —
including one deliberately below its ReFuelEU mandate to demonstrate the compliance flag).

## Tests

```bash
cd backend && source .venv/bin/activate && pytest
```

Covers the GHG intensity formula, ASTM pathway conformance checks, the ReFuelEU mandate
schedule, and a full router smoke test against the seeded database.
