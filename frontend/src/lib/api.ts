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
