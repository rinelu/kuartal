/**
 * Fetches the data-contract shape from the Python backend
 * (dashboard.md §3 / kuartal/api/schemas.py). This is the ONLY file that
 * should know the API's base URL or endpoint paths - components take
 * plain data as props, they never fetch.
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${path} -> ${res.status}`);
  }
  return res.json();
}

/**
 * @returns {Promise<{companies: object[], recentVerdicts: object[], metrics: object}>}
 * `scenario="empty"` exercises the empty-watchlist state (dashboard.md §4).
 */
export function getWatchlist(scenario = "default") {
  const query = scenario !== "default" ? `?scenario=${scenario}` : "";
  return request(`/api/watchlist${query}`);
}

/** @returns {Promise<object>} single CompanyCard for `ticker`. */
export function getCompany(ticker) {
  return request(`/api/company/${ticker}`);
}

/**
 * Backs PipelineStrip. Not part of the §3 contract - poll this
 * separately while a run is in flight.
 * @returns {Promise<{ticker: string, steps: {name: string, status: string}[]}>}
 */
export function getPipelineStatus(ticker) {
  return request(`/api/pipeline-status/${ticker}`);
}
