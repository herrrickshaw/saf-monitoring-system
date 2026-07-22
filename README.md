# SAF Monitoring System

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/herrrickshaw/saf-monitoring-system/blob/main/notebooks/colab_test.ipynb)

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
- `backend/app/calculations/corsia.py` — CORSIA L_CEF methodology, the 89 gCO2e/MJ baseline,
  the 10% minimum-reduction eligibility threshold (Annex 16 Vol IV, Sustainability Criterion
  1.1), and ICAO's published default Core LCA values by feedstock/pathway, sourced from the
  ICAO "CORSIA Default Life Cycle Emissions Values for CORSIA Eligible Fuels" document
  (8th Edition, 19 Nov 2025): https://www.icao.int/CORSIA/corsia-eligible-fuels

### RED III vs CORSIA — two distinct comparators

These are separate regulatory regimes with different baselines and are **not**
interchangeable:

| | RED III / ReFuelEU (EU) | CORSIA (ICAO) |
|---|---|---|
| Baseline | 94 gCO2eq/MJ | 89 gCO2e/MJ |
| Metric | `ghg_intensity` / `ghg_savings_pct` on `SAFCertificate` | `corsia_lcef` / `corsia_reduction_pct` |
| Eligibility | feeds ReFuelEU blending-mandate compliance | ≥10% reduction (`corsia_eligible`) |
| Feeds | `BlendingRecord` compliance flag | `CarbonCreditLedger` tCO2e credits |

The carbon-credit ledger (`CarbonCreditLedger.tco2e_saved`) is computed against the
CORSIA baseline/L_CEF, not the RED III intensity — a batch must be `corsia_eligible`
before a credit entry can be generated for it.

### India CCTS / Indian Carbon Market — forward-compatible, not yet active

`backend/app/calculations/ccts_icm.py` implements the accounting mechanics of India's
domestic **Carbon Credit Trading Scheme (CCTS)** / **Indian Carbon Market (ICM)**, run by
the Bureau of Energy Efficiency (BEE) under the Energy Conservation (Amendment) Act, 2022:
1 Carbon Credit Certificate (CCC) = 1 tCO2e, with obligated entities earning surplus CCCs
for beating their GHG emission-intensity target and owing CCCs for missing it.

**SAF/aviation fuel production is not yet a notified CCTS sector** (Compliance Mechanism
covers Aluminium, Chlor Alkali, Cement, Fertiliser, Iron & Steel, Pulp & Paper,
Petrochemicals, Petroleum Refinery, Textile; Offset Mechanism Phase I/II covers Energy,
Industries, Agriculture, Waste handling, Forestry, Transport, Fugitive emissions,
Construction, Solvent use, Carbon capture/storage/removal — no aviation category yet).
This module is built ahead of that notification so the platform is ready the moment BEE
extends CCTS to SAF: `GET /api/compliance/ccts-icm/status` reports current coverage, and
`POST /api/compliance/ccts-icm/estimate` runs a what-if CCC surplus/deficit calculation
(informational only, since no official target intensity exists yet). Flip
`SAF_SECTOR_NOTIFIED` in `ccts_icm.py` once BEE publishes one. Source:
https://beeindia.gov.in

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
