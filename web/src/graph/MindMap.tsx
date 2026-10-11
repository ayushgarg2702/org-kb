import cytoscape, { Core } from "cytoscape";
import { useEffect, useRef } from "react";
import type { GraphPayload } from "../api/client";

type Props = {
  data: GraphPayload;
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
};

function colorFor(origin?: string) {
  if (origin === "verified" || origin === "statically_declared") return "#3ecf8e";
  if (origin === "runtime_observed" || origin === "observed") return "#3d9cf0";
  if (origin === "inferred" || origin === "parser_extracted" || origin === "model_inferred") return "#f0b429";
  if (origin === "conflicting") return "#ef6b6b";
  return "#8b95a1";
}

export function MindMap({ data, onSelect, onExpand }: Props) {
  const ref = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: ref.current,
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              color: "#e7eef7",
              "background-color": "data(color)",
              "font-size": "10px",
              "text-wrap": "wrap",
              "text-max-width": "80px",
              width: "28px",
              height: "28px",
            },
          },
          {
            selector: "edge",
            style: {
              width: 2,
              "line-color": "#4a5a6a",
              "target-arrow-color": "#4a5a6a",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-size": "8px",
              color: "#9aabb8",
            },
          },
        ],
        layout: { name: "cose", animate: false },
      });
      cyRef.current.on("tap", "node", (evt) => {
        const id = evt.target.id();
        onSelect(id);
        onExpand(id);
      });
    }
    const cy = cyRef.current;
    cy.elements().remove();
    cy.add(
      data.nodes.map((n) => ({
        group: "nodes" as const,
        data: {
          id: n.id,
          label: n.label,
          color: colorFor(n.origin || n.confidence),
        },
      })),
    );
    cy.add(
      data.edges.map((e) => ({
        group: "edges" as const,
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
        },
      })),
    );
    cy.layout({ name: "cose", animate: true, animationDuration: 300 }).run();
  }, [data, onExpand, onSelect]);

  return <div id="cy" ref={ref} aria-label="Organization mind map" />;
}
