/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { NetworkNode, NetworkEdge, AgentState } from '../types/models';
import { getClusterColor } from '../utils/colorScales';

interface UseD3NetworkProps {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  agentStates: AgentState[];
  width: number;
  height: number;
}

export const useD3Network = ({ nodes, edges, agentStates, width, height }: UseD3NetworkProps) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0 || width === 0 || height === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    // Merge agent states into nodes for coloring by cluster
    const agentMap = new Map(agentStates.map(a => [a.agent_id, a]));
    const graphNodes = nodes.map(n => ({
      ...n,
      cluster_id: agentMap.get(n.id)?.cluster_id ?? 0
    }));

    // Copy edges to prevent D3 from mutating the original props
    const graphEdges = edges.map(e => ({ ...e }));

    const g = svg.append("g");

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    svg.call(zoom);

    // Force Simulation
    const simulation = d3.forceSimulation(graphNodes as any)
      .force("link", d3.forceLink(graphEdges).id((d: any) => d.id).distance(20))
      .force("charge", d3.forceManyBody().strength(-30))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius((d: any) => 3 + d.centrality * 12 + 2));

    // Links
    const link = g.append("g")
      .selectAll("line")
      .data(graphEdges)
      .join("line")
      .attr("stroke", "var(--color-hairline)")
      .attr("stroke-width", 1)
      .attr("stroke-opacity", 0.6);

    // Nodes
    const node = g.append("g")
      .selectAll("circle")
      .data(graphNodes as any)
      .join("circle")
      .attr("r", (d: any) => 3 + d.centrality * 12)
      .attr("fill", (d: any) => getClusterColor(d.cluster_id))
      .attr("stroke", "var(--color-paper)")
      .attr("stroke-width", 1);

    // Tooltips (simple title for now, can be expanded to HTML tooltip)
    node.append("title")
      .text((d: any) => `Agent ${d.id}\nCommunity: ${d.community_id}\nCluster: ${d.cluster_id}`);

    // Tick update
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y);
    });

    // Handle Reduced Motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      simulation.stop();
      simulation.tick(300); // Fast-forward
      simulation.tick(300); // Fast-forward
      // Manually trigger render by firing the tick listener callback if needed
      // Actually we don't need to manually trigger if we just update the attr directly
      // But we can just restart it with 0 alpha.
      link.attr("x1", (d: any) => d.source.x).attr("y1", (d: any) => d.source.y).attr("x2", (d: any) => d.target.x).attr("y2", (d: any) => d.target.y);
      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [nodes, edges, agentStates, width, height]);

  return svgRef;
};
