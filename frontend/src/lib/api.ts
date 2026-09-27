const API_BASE = '/api';

export async function searchLocations(query: string) {
  const res = await fetch(`${API_BASE}/locations/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return [];
  return await res.json();
}

export async function fetchDomainGIS(domainId: string = 'tehri', riverName?: string) {
  let url = `${API_BASE}/locations/domain/${encodeURIComponent(domainId)}`;
  if (riverName) {
    url += `?river_name=${encodeURIComponent(riverName)}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch GIS layers');
  return await res.json();
}

export async function startSimulation(params: any) {
  const res = await fetch(`${API_BASE}/simulations/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail?.errors?.join(', ') || errData.detail?.warnings?.join(', ') || 'Simulation launch failed');
  }
  return await res.json();
}

export async function pollSimulationStatus(jobId: string) {
  const res = await fetch(`${API_BASE}/simulations/${jobId}/status`);
  if (!res.ok) throw new Error('Failed to poll job status');
  return await res.json();
}

export async function fetchSimulationResults(jobId: string) {
  const res = await fetch(`${API_BASE}/simulations/${jobId}/results`);
  if (!res.ok) throw new Error('Failed to fetch simulation results');
  return await res.json();
}

export async function fetchSentinel1Observation() {
  const res = await fetch(`${API_BASE}/observation/sentinel1`);
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchValidationMetrics(jobId: string) {
  const res = await fetch(`${API_BASE}/observation/validate/${jobId}`);
  if (!res.ok) return { available: false, reason: 'Validation endpoint error' };
  return await res.json();
}

export async function fetchModelComparison(params: any) {
  const res = await fetch(`${API_BASE}/comparison/sph-vs-delft3d`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to compute model comparison');
  return await res.json();
}

// ============================================================
// DATA SOURCES REGISTRY & MANIFEST API
// ============================================================

export async function fetchDataProviders(params?: { q?: string; category?: string; protocol?: string; authority?: string }) {
  const query = new URLSearchParams();
  if (params?.q) query.set('q', params.q);
  if (params?.category) query.set('category', params.category);
  if (params?.protocol) query.set('protocol', params.protocol);
  if (params?.authority) query.set('authority', params.authority);

  const res = await fetch(`${API_BASE}/datasources/search?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch data providers');
  return await res.json();
}

export async function fetchDataCategories() {
  const res = await fetch(`${API_BASE}/datasources/categories`);
  if (!res.ok) throw new Error('Failed to fetch category statistics');
  return await res.json();
}

export async function fetchDataReadiness(damName: string = 'Tehri Dam', riverName: string = 'Bhagirathi River') {
  const res = await fetch(`${API_BASE}/datasources/readiness?dam_name=${encodeURIComponent(damName)}&river_name=${encodeURIComponent(riverName)}`);
  if (!res.ok) throw new Error('Failed to fetch data readiness report');
  return await res.json();
}

export async function fetchSimulationManifest(damName: string = 'Tehri Dam', riverName: string = 'Bhagirathi River') {
  const res = await fetch(`${API_BASE}/datasources/manifest/simulation?dam_name=${encodeURIComponent(damName)}&river_name=${encodeURIComponent(riverName)}`);
  if (!res.ok) throw new Error('Failed to fetch simulation input manifest');
  return await res.json();
}

export async function fetchValidationManifest(jobId: string = 'JOB-SAR-VAL-001') {
  const res = await fetch(`${API_BASE}/datasources/manifest/validation?job_id=${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error('Failed to fetch validation manifest');
  return await res.json();
}

