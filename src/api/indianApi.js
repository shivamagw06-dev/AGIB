// All market-data requests go through the local Express proxy.
// This deliberately keeps INDIANAPI_KEY off the public React bundle.
const BASE_URL = "/api";

async function request(endpoint) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`Market data request failed (${response.status})${detail ? `: ${detail.slice(0, 120)}` : ""}`);
  }

  return response.json();
}

export const getIndices = () => request("/indices");
export const getTrending = () => request("/trending?exchange=NSE");
export const getNews = () => request("/news?page_no=1&size=5");
export const getCommodities = () => request("/commodities");
