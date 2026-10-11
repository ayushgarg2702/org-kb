import React, { useEffect, useState } from "react";
import { fetchPersonalDashboard } from "./api/dashboardClient";

/** Personal dashboard page — entry for the "make dashboard faster" golden path. */
export function PersonalDashboard() {
  const [data, setData] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPersonalDashboard()
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>Loading personal dashboard…</div>;
  return (
    <main>
      <h1>Personal Dashboard</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  );
}
