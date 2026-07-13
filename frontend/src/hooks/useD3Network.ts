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
  onSelect?: (agentId: number) => void;
  showLabels?: boolean;
}

export const useD3Network = ({ nodes, edges, agentStates, width, height, onSelect, showLabels = false }: UseD3NetworkProps) => {
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
      .force("collide", d3.forceCollide().radius((d: any) => 3 + d.centrality * 12 + 2))
      .force("x", d3.forceX(width / 2).strength(0.05))
      .force("y", d3.forceY(height / 2).strength(0.05));

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
      .attr("stroke-width", 1)
      .attr("tabindex", 0)
      .attr("role", "button")
      .attr("aria-label", (d: any) => `Inspect speaker ${d.id}`)
      .on("click", (_event, d: any) => onSelect?.(d.id))
      .on("keydown", (event: KeyboardEvent, d: any) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect?.(d.id); } });

    if (showLabels) g.append('g').selectAll('text').data(graphNodes as any).join('text').text((d: any) => d.id).attr('font-size', 9).attr('fill', '#525252').attr('text-anchor', 'middle').attr('dy', -8).attr('pointer-events', 'none');

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

    const zoomToFit = () => {
      if (graphNodes.length === 0) return;
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      graphNodes.forEach((n: any) => {
        const r = 3 + n.centrality * 12;
        if (n.x - r < minX) minX = n.x - r;
        if (n.x + r > maxX) maxX = n.x + r;
        if (n.y - r < minY) minY = n.y - r;
        if (n.y + r > maxY) maxY = n.y + r;
      });
      const dx = maxX - minX;
      const dy = maxY - minY;
      const x = (minX + maxX) / 2;
      const y = (minY + maxY) / 2;
      
      if (dx === 0 || dy === 0 || !isFinite(dx)) return;
      
      // Calculate scale to fit within viewport with some padding (90% of width/height)
      const scale = Math.max(0.1, Math.min(4, 0.9 / Math.max(dx / width, dy / height)));
      const translate = [width / 2 - scale * x, height / 2 - scale * y];
      
      svg.transition().duration(750).call(zoom.transform as any, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
    };

    simulation.on("end", zoomToFit);

    // Handle Reduced Motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      simulation.stop();
      simulation.tick(300); // Fast-forward
      simulation.tick(300); // Fast-forward
      link.attr("x1", (d: any) => d.source.x).attr("y1", (d: any) => d.source.y).attr("x2", (d: any) => d.target.x).attr("y2", (d: any) => d.target.y);
      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
      zoomToFit();
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [nodes, edges, agentStates, width, height, onSelect, showLabels]);

  return svgRef;
};
