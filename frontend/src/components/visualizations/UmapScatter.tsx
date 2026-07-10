import React, { useRef } from 'react';
import { useD3Scatter } from '../../hooks/useD3Scatter';
import { useResizeObserver } from '../../hooks/useResizeObserver';
import { useSimulation } from '../../contexts/SimulationContext';
import { Slider } from '../core/Slider';

export const UmapScatter: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { width, height } = useResizeObserver(containerRef);
  const { umapData, result, selectedTimestep, setSelectedTimestep } = useSimulation();

  const timesteps = umapData ? Object.keys(umapData).map(Number).sort((a,b)=>a-b) : [];
  const coords = umapData ? umapData[selectedTimestep.toString()] : [];
  const agentStates = result?.final_agent_states || [];

  const svgRef = useD3Scatter({ coords, agentStates, width, height });

  if (!umapData) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 'var(--spacing-16)' }}>
        <span className="spinner" style={{ borderColor: 'rgba(39, 36, 33, 0.2)', borderTopColor: 'var(--color-ink)', width: '32px', height: '32px' }}></span>
        <p style={{ color: 'var(--color-stone)' }}>Computing UMAP projection...</p>
      </div>
    );
  }

  // Find the index of the selected timestep for the slider
  const currentIndex = timesteps.indexOf(selectedTimestep);

  return (
    <div style={{ width: '100%', height: '500px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-16)' }}>
        <h3 style={{ fontFamily: 'var(--font-egyptienne-f-lt)', fontSize: 'var(--text-heading-sm)' }}>
          Accent Space (UMAP)
        </h3>
        {timesteps.length > 0 && (
          <div style={{ width: '300px' }}>
            <Slider
              label="Timestep"
              min={0}
              max={timesteps.length - 1}
              step={1}
              value={currentIndex}
              onChange={(val) => setSelectedTimestep(timesteps[val])}
              formatValue={(val) => `t = ${timesteps[val]}`}
            />
          </div>
        )}
      </div>
      <div ref={containerRef} style={{ flex: 1, backgroundColor: 'var(--surface-canvas)', border: '1px solid var(--color-paper-cool)', borderRadius: 'var(--radius-cards)', overflow: 'hidden' }}>
        <svg ref={svgRef} width="100%" height="100%" style={{ display: 'block' }} />
      </div>
    </div>
  );
};
