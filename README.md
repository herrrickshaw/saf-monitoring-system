# SAF Monitoring System

<!-- how-to-use-with-ai -->
> **New here?** See [How to use this repo with AI (Claude, Gemini, ChatGPT)](HOW_TO_USE_WITH_AI.md) — clone it, paste it into an AI tool, and ask in plain English.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/herrrickshaw/saf-monitoring-system/blob/main/notebooks/colab_test.ipynb)

A compliance monitoring platform (FastAPI + React, SQLite) for Sustainable Aviation Fuel plant and
supply-chain operations. It tracks feedstock arrivals, links them to production batches, computes GHG
intensity and CORSIA life-cycle values, checks ASTM D7566 pathway conformance and ReFuelEU blending
mandates, keeps a CORSIA carbon-credit ledger, and produces per-airline PDF/Excel supply reports.
Runs on seeded mock data out of the box.

> Status: active, demonstration-grade. Regulatory values are editable defaults, not legal advice; confirm
> them against current official sources before any real compliance reporting (see "Regulatory basis").

## What it does
- Records feedstocks and deliveries, production batches and ASTM pathways (`/api/feedstock`, `/api/production`).
- Generates a SAF certificate per batch: RED III GHG intensity/savings and CORSIA L_CEF/reduction/eligibility (`/api/certificates`).
- Ledgers CORSIA tCO2e credits per airline delivery, only for CORSIA-eligible batches (`/api/carbon-credits`).
- Flags airport-level ReFuelEU blending compliance against the yearly mandate (`/api/compliance/blending`).
- Estimates India CCTS/ICM surplus or deficit and illustrative bio-carbon credits (`/api/compliance/ccts-icm/*`, `/api/compliance/bio-carbon/*`).
- Downloads traceable airline reports as PDF or Excel (`/api/airlines/{id}/report`).

## Quick start
```bash
git clone https://github.com/herrrickshaw/saf-monitoring-system.git
cd saf-monitoring-system
./run_app.sh        # needs Python 3.10+ and Node 18+
```
`run_app.sh` creates `backend/.venv`, installs dependencies, starts the API on `:8000`
(Swagger at `http://localhost:8000/docs`) and the Vite frontend on `:5173`. On first run the backend
seeds ~12 months of mock data: 3 feedstocks, 36 production batches with certificates, 3 airline offtake
contracts, a CORSIA credit ledger, and blending records for 3 airports (one deliberately below its
ReFuelEU mandate to demonstrate the compliance flag).

## How it works
```
React (frontend/src/pages) --REST--> FastAPI routers --> calculations (pure) --> SQLAlchemy/SQLite
```
| Stage | Module | Output |
|---|---|---|
| Persistence | `backend/app/db.py`, `models.py` | SQLite (`SAF_DB_PATH`), `persist()` commit helper |
| GHG / CORSIA / ASTM / mandate maths | `backend/app/calculations/*.py` | pure functions, no DB or HTTP types |
| Certificate assembly | `calculations/certification.py` | `CertificateMetrics` consumed by `routers/certificates.py` |
| HTTP layer | `backend/app/routers/*.py` | JSON endpoints; compliance routes split into `compliance_blending/_ccts/_bio_carbon` |
| Airline reports | `backend/app/reports/airline_report.py` | `collect_report_data` (query + format) then `render_pdf` / `render_excel` |
| Mock data | `backend/app/seed/mock_data.py` | seeded on empty DB (RNG seed 42) |

Design decisions: calculation modules stay free of FastAPI/SQLAlchemy so they can be unit-tested and
reviewed against the regulations in isolation; routers only translate between HTTP and those functions.

## Regulatory basis

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

## Repository layout
| Path | Purpose |
|---|---|
| `backend/app/` | FastAPI app: `main.py`, `db.py`, `models.py`, `routers/`, `schemas/`, `calculations/`, `reports/`, `seed/` |
| `backend/tests/` | pytest suite incl. golden snapshots (`tests/golden/`) of seeded API output and the OpenAPI schema |
| `frontend/` | React + Vite + Tailwind single-page app, one page per tab |
| `notebooks/colab_test.ipynb` | Colab smoke notebook |
| `run_app.sh` | Starts backend and frontend together |
| `pyproject.toml`, `.github/workflows/ci.yml` | ruff + pytest config; CI runs ruff, pytest and the frontend build |

## Data sources
| Source | What is taken | Access route | Licence / caveat |
|---|---|---|---|
| ICAO CORSIA default LCA values, 8th Ed. (19 Nov 2025) | Core LCA values by pathway/feedstock, 89 gCO2e/MJ baseline | Hard-coded in `calculations/corsia.py` | Check the current ICAO edition before real use |
| RED III / ReFuelEU | 94 gCO2eq/MJ comparator, yearly mandate shares | Hard-coded in `ghg.py`, `mandate_schedule.py` | Editable defaults; confirm against current Delegated/Implementing Regulations |
| ASTM D7566 | Approved pathways and max blend ratios | `calculations/astm_pathways.py` | Confirm against the current standard edition |
| BEE / CCTS | Sector lists, 1 CCC = 1 tCO2e | `calculations/ccts_icm.py` (https://beeindia.gov.in) | SAF not yet a notified sector |
| UPNEDA bio-carbon calculator | Structure only | `calculations/biocarbon_estimator.py` | Factors are placeholders, not UPNEDA's real values |

## Configuration
| Variable | Default | Meaning |
|---|---|---|
| `SAF_DB_PATH` | `backend/saf.db` | SQLite file location |

No secrets are required or committed. CORS allows `localhost:5173` and `localhost:3000`.

## Testing
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt ruff
pytest -q          # from the repo root; ruff check .
```
Covers the GHG formula, ASTM conformance, the mandate schedule, CORSIA and CCTS maths, certificate
assembly, report rendering, a router smoke test on the seeded DB, and golden snapshots proving API output
is unchanged by refactors. The frontend is verified with `cd frontend && npm ci && npm run build`.

## Limitations and known issues
- Mock data and illustrative factors only; not a certified compliance tool.
- Requires Python 3.10+ (`X | None` annotations are evaluated by FastAPI/Pydantic).
- SQLAlchemy models use `datetime.utcnow`, which is deprecated in newer Pythons (warning only).
- `SAF_SECTOR_NOTIFIED` in `ccts_icm.py` must be flipped manually once BEE notifies SAF under CCTS.
- Bio-carbon per-feedstock factors are order-of-magnitude placeholders.

## Licence
No licence file yet — all rights reserved.
