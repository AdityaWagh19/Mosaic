import React from 'react';
import { MainLayout } from '../layouts/MainLayout';
import { Sidebar } from '../layouts/Sidebar';
import { ControlPanel } from '../components/simulation/ControlPanel';
import { useSimulation } from '../contexts/SimulationContext';
import { NetworkGraph } from '../components/visualizations/NetworkGraph';
import { TimeSeriesChart } from '../components/visualizations/TimeSeriesChart';
import { UmapScatter } from '../components/visualizations/UmapScatter';

export const Dashboard: React.FC = () => {
  const { globalError, isSimulating, result } = useSimulation();

  return (
    <MainLayout
      sidebar={
        <Sidebar>
          <ControlPanel />
        </Sidebar>
      }
    >
      {globalError && (
        <div style={{ padding: 'var(--spacing-16)', backgroundColor: 'var(--color-mist)', color: 'var(--color-ink)', borderRadius: 'var(--radius-cards)', marginBottom: 'var(--spacing-24)' }}>
          <strong>Error:</strong> {globalError}
        </div>
      )}

      {isSimulating ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 'var(--spacing-16)' }}>
          <span className="spinner" style={{ borderColor: 'rgba(39, 36, 33, 0.2)', borderTopColor: 'var(--color-ink)', width: '32px', height: '32px' }}></span>
          <p style={{ color: 'var(--color-stone)' }}>Simulating agents...</p>
        </div>
      ) : !result ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <h2 style={{ color: 'var(--color-stone)', textAlign: 'center' }}>
            Adjust parameters and<br/>Run Simulation to begin
          </h2>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--section-gap)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '1px solid var(--color-paper-warm)', paddingBottom: 'var(--spacing-16)' }}>
            <h2 style={{ fontFamily: 'var(--font-egyptienne-f-lt)', fontSize: 'var(--text-heading-lg)' }}>
              Simulation Result
            </h2>
            <div style={{ display: 'flex', gap: 'var(--spacing-16)' }}>
              <div className="badge">Converged: {result.metrics.converged ? 'Yes' : 'No'}</div>
              <div className="badge">Time: {result.metrics.convergence_time} steps</div>
            </div>
          </div>
          
          <NetworkGraph 
            nodes={result.network.nodes} 
            edges={result.network.edges} 
            agentStates={result.final_agent_states} 
          />
          
          <TimeSeriesChart data={result.timeline} />
          
          <UmapScatter />
        </div>
      )}
    </MainLayout>
  );
};
