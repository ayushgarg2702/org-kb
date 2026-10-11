/** API client for the personal dashboard. Calls backend /api/dashboard. */
export async function fetchPersonalDashboard(): Promise<unknown> {
  const response = await fetch("/api/dashboard", {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`dashboard request failed: ${response.status}`);
  }
  return response.json();
}
