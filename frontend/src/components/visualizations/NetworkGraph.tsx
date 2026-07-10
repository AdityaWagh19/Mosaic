import React, { useRef } from 'react';
import { useD3Network } from '../../hooks/useD3Network';
import { useResizeObserver } from '../../hooks/useResizeObserver';
import { NetworkNode, NetworkEdge, AgentState } from '../../types/models';

interface NetworkGraphProps {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  agentStates: AgentState[];
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({ nodes, edges, agentStates }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { width, height } = useResizeObserver(containerRef);
  
  const svgRef = useD3Network({ nodes, edges, agentStates, width, height });

  return (
    <div style={{ width: '100%', height: '500px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: 'var(--spacing-16)', fontFamily: 'var(--font-egyptienne-f-lt)', fontSize: 'var(--text-heading-sm)' }}>
        Network Structure
      </h3>
      <div ref={containerRef} style={{ flex: 1, backgroundColor: 'var(--surface-canvas)', border: '1px solid var(--color-paper-cool)', borderRadius: 'var(--radius-cards)', overflow: 'hidden' }}>
        <svg ref={svgRef} width="100%" height="100%" style={{ display: 'block' }} />
      </div>
    </div>
  );
};
