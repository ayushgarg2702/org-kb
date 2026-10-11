import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ask,
  fetchEvidence,
  fetchNeighbors,
  fetchNode,
  fetchOverview,
  search,
  type GraphPayload,
} from "../api/client";
import { MindMap } from "../graph/MindMap";

function mergeGraph(base: GraphPayload, extra: GraphPayload): GraphPayload {
  const nodes = new Map(base.nodes.map((n) => [n.id, n]));
  extra.nodes.forEach((n) => nodes.set(n.id, n));
  const edges = new Map(base.edges.map((e) => [e.id, e]));
  extra.edges.forEach((e) => edges.set(e.id, e));
  return {
    nodes: [...nodes.values()],
    edges: [...edges.values()],
    partial: base.partial || extra.partial,
    coverage: base.coverage,
  };
}

export function App() {
  const [graph, setGraph] = useState<GraphPayload>({ nodes: [], edges: [] });
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [evidence, setEvidence] = useState<Array<Record<string, unknown>>>([]);
  const [q, setQ] = useState("Make the personal dashboard load faster.");
  const [answer, setAnswer] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const partial = Boolean(graph.partial);

  useEffect(() => {
    fetchOverview()
      .then(setGraph)
      .catch((e: Error) => setError(e.message));
  }, []);

  const onExpand = useCallback(async (id: string) => {
    const neigh = await fetchNeighbors(id);
    setGraph((g) => mergeGraph(g, neigh));
    const node = await fetchNode(id);
    setSelected(node);
    const ev = await fetchEvidence(id);
    setEvidence(ev.evidence || []);
  }, []);

  const onSearch = async () => {
    const res = await search(q);
    if (res.results[0]) {
      await onExpand(res.results[0].id);
    }
  };

  const onAsk = async () => {
    const res = await ask(q);
    setAnswer(String(res.answer || ""));
    const ents = (res.entities as Array<{ id: string }>) || [];
    if (ents[0]) await onExpand(ents[0].id);
  };

  const banner = useMemo(
    () =>
      partial
        ? "Published map is explicitly incomplete — gaps and unsupported files are recorded in coverage."
        : null,
    [partial],
  );

  return (
    <div className="app" style={{ display: "grid", gridTemplateRows: banner ? "auto 1fr" : "1fr" }}>
      {banner ? <div className="banner">{banner}</div> : null}
      <div className="app">
        <aside className="sidebar">
          <h1>Org Brain</h1>
          <p className="meta">Progressive mind map — expand on click. Color is not the only signal.</p>
          <div className="search">
            <input value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search or question" />
          </div>
          <div className="search">
            <button type="button" onClick={onSearch}>
              Search
            </button>
            <button type="button" onClick={onAsk}>
              Ask
            </button>
          </div>
          <h2>Legend</h2>
          <ul className="legend">
            <li>
              <span className="swatch verified" /> Verified / repository
            </li>
            <li>
              <span className="swatch inferred" /> Inferred / parser
            </li>
            <li>
              <span className="swatch unknown" /> Unknown / unresolved
            </li>
            <li>
              <span className="swatch conflict" /> Conflicting
            </li>
          </ul>
          {error ? <p className="meta">Error: {error}</p> : null}
          {answer ? (
            <>
              <h2>Answer</h2>
              <p className="meta">{answer}</p>
            </>
          ) : null}
        </aside>
        <MindMap data={graph} onSelect={() => undefined} onExpand={onExpand} />
        <aside className="details">
          <h2>Entity details</h2>
          {selected ? (
            <>
              <p>
                <strong>{String(selected.name)}</strong> ({String(selected.type)})
              </p>
              <pre className="meta">{JSON.stringify(selected.source_refs, null, 2)}</pre>
              <div className="evidence">
                <h2>Evidence</h2>
                {evidence.length === 0 ? <p className="meta">No source-span evidence.</p> : null}
                {evidence.map((e) => (
                  <div key={String(e.id)}>
                    <div className="meta">
                      {String(e.repository_id)}:{String(e.path)}:{String(e.start_line)}-{String(e.end_line)}
                    </div>
                    <pre>{String(e.excerpt || "")}</pre>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="meta">Select a node to inspect provenance and evidence.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
