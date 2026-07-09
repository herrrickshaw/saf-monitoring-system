const BASE_URL = "/api";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return res.json();
}

export function fetchDashboardSummary() {
  return apiFetch("/dashboard/summary");
}

export function fetchFeedstocks() {
  return apiFetch("/feedstock");
}

export function fetchFeedstockDeliveries() {
  return apiFetch("/feedstock/deliveries");
}

export function createFeedstockDelivery(payload) {
  return apiFetch("/feedstock/deliveries", { method: "POST", body: JSON.stringify(payload) });
}

export function fetchProductionBatches() {
  return apiFetch("/production/batches");
}

export function fetchASTMPathways() {
  return apiFetch("/production/pathways");
}

export function createProductionBatch(payload) {
  return apiFetch("/production/batches", { method: "POST", body: JSON.stringify(payload) });
}

export function fetchCertificates() {
  return apiFetch("/certificates");
}

export function generateCertificate(batchId) {
  return apiFetch(`/certificates/generate/${batchId}`, { method: "POST" });
}

export function fetchCarbonCreditLedger() {
  return apiFetch("/carbon-credits/ledger");
}

export function generateCarbonCredit(airlineDeliveryId) {
  return apiFetch(`/carbon-credits/generate/${airlineDeliveryId}`, { method: "POST" });
}

export function fetchAirlines() {
  return apiFetch("/airlines");
}

export function fetchAirlineDeliveries() {
  return apiFetch("/airlines/deliveries");
}

export function airlineReportUrl(offtakeId, start, end, fmt) {
  const params = new URLSearchParams({ start, end, fmt });
  return `${BASE_URL}/airlines/${offtakeId}/report?${params.toString()}`;
}

export function fetchBlendingCompliance(airport, year) {
  const params = new URLSearchParams();
  if (airport) params.set("airport", airport);
  if (year) params.set("year", year);
  const qs = params.toString();
  return apiFetch(`/compliance/blending${qs ? `?${qs}` : ""}`);
}
