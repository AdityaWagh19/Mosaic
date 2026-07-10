import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { AgentState } from '../../types/models';
import { getClusterColor } from '../../utils/colorScales';

interface UseD3ScatterProps {
  coords: [number, number][];
  agentStates: AgentState[];
  width: number;
  height: number;
}

export const useD3Scatter = ({ coords, agentStates, width, height }: UseD3ScatterProps) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || coords.length === 0 || width === 0 || height === 0) return;

    const svg = d3.select(svgRef.current);
    
    // Setup scales
    const xExtent = d3.extent(coords, d => d[0]) as [number, number];
    const yExtent = d3.extent(coords, d => d[1]) as [number, number];
    
    // Add padding (10%)
    const paddingX = (xExtent[1] - xExtent[0]) * 0.1;
    const paddingY = (yExtent[1] - yExtent[0]) * 0.1;

    const xScale = d3.scaleLinear()
      .domain([xExtent[0] - paddingX, xExtent[1] + paddingX])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - paddingY, yExtent[1] + paddingY])
      .range([height, 0]);

    // Initial render
    if (svg.selectAll("g.scatter-container").empty()) {
      const g = svg.append("g").attr("class", "scatter-container");

      // Zoom behavior
      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.5, 10])
        .on("zoom", (event) => {
          g.attr("transform", event.transform);
        });
      svg.call(zoom);

      // Create nodes
      g.selectAll("circle")
        .data(coords)
        .join("circle")
        .attr("r", 4)
        .attr("fill", (d, i) => getClusterColor(agentStates[i]?.cluster_id ?? 0))
        .attr("stroke", "var(--color-white)")
        .attr("stroke-width", 0.5)
        .attr("cx", d => xScale(d[0]))
        .attr("cy", d => yScale(d[1]))
        .append("title")
        .text((d, i) => `Agent ${agentStates[i]?.agent_id}`);
    } else {
      // Transition update
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const duration = prefersReducedMotion ? 0 : 800;

      svg.select("g.scatter-container").selectAll("circle")
        .data(coords)
        .transition()
        .duration(duration)
        .ease(d3.easeCubicOut)
        .attr("cx", d => xScale(d[0]))
        .attr("cy", d => yScale(d[1]));
    }
  }, [coords, agentStates, width, height]);

  return svgRef;
};
