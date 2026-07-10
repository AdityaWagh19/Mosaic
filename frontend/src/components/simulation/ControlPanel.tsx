import React, { useEffect, useState } from 'react';
import { useSimulation } from '../../contexts/SimulationContext';
import { fetchTopologies } from '../../api/client';
import { Dropdown } from '../core/Dropdown';
import { Slider } from '../core/Slider';
import { Button } from '../core/Button';

export const ControlPanel: React.FC = () => {
  const { config, setConfig, isSimulating, executeRun } = useSimulation();
  const [topologies, setTopologies] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchTopologies().then(setTopologies).catch(console.error);
  }, []);

  const topoOptions = Object.keys(topologies).map(k => ({
    value: k,
    label: topologies[k].desc || k
  }));

  const activeParams = topologies[config.topology]?.params || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-32)' }}>
      <Dropdown
        label="Network Topology"
        value={config.topology}
        options={topoOptions}
        onChange={(val) => setConfig({ ...config, topology: val })}
        disabled={isSimulating}
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-16)' }}>
        <h3 style={{ fontSize: 'var(--text-caption)', letterSpacing: 'var(--tracking-caption)', textTransform: 'uppercase', color: 'var(--color-stone)' }}>
          Global Parameters
        </h3>
        <Slider
          label="N (Agents)"
          min={50} max={500} step={10}
          value={config.N}
          onChange={(val) => setConfig({ ...config, N: val })}
          disabled={isSimulating}
        />
        <Slider
          label="T (Timesteps)"
          min={100} max={10000} step={100}
          value={config.T}
          onChange={(val) => setConfig({ ...config, T: val })}
          disabled={isSimulating}
        />
        <Slider
          label="Gamma (Assimilation)"
          min={0.1} max={2.0} step={0.1}
          value={config.gamma}
          onChange={(val) => setConfig({ ...config, gamma: val })}
          disabled={isSimulating}
        />
        <Slider
          label="Theta (Threshold)"
          min={0.1} max={1.0} step={0.1}
          value={config.theta}
          onChange={(val) => setConfig({ ...config, theta: val })}
          disabled={isSimulating}
        />
        <Slider
          label="Sigma (Noise)"
          min={0.0} max={0.1} step={0.01}
          value={config.sigma}
          onChange={(val) => setConfig({ ...config, sigma: val })}
          disabled={isSimulating}
        />
      </div>

      {activeParams.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-16)' }}>
          <h3 style={{ fontSize: 'var(--text-caption)', letterSpacing: 'var(--tracking-caption)', textTransform: 'uppercase', color: 'var(--color-stone)' }}>
            Topology Parameters
          </h3>
          {activeParams.includes('p_er') && (
            <Slider label="P (Erdös-Rényi)" min={0.01} max={0.2} step={0.01} value={config.p_er!} onChange={(v) => setConfig({...config, p_er: v})} disabled={isSimulating} />
          )}
          {activeParams.includes('k_ws') && (
            <Slider label="K (Watts-Strogatz)" min={2} max={20} step={2} value={config.k_ws!} onChange={(v) => setConfig({...config, k_ws: v})} disabled={isSimulating} />
          )}
          {activeParams.includes('p_rewire') && (
            <Slider label="P Rewire" min={0} max={1} step={0.05} value={config.p_rewire!} onChange={(v) => setConfig({...config, p_rewire: v})} disabled={isSimulating} />
          )}
          {activeParams.includes('m_ba') && (
            <Slider label="M (Barabási-Albert)" min={1} max={10} step={1} value={config.m_ba!} onChange={(v) => setConfig({...config, m_ba: v})} disabled={isSimulating} />
          )}
          {activeParams.includes('n_communities') && (
            <Slider label="Communities" min={2} max={10} step={1} value={config.n_communities!} onChange={(v) => setConfig({...config, n_communities: v})} disabled={isSimulating} />
          )}
          {activeParams.includes('p_in') && (
            <Slider label="P (In)" min={0.1} max={1.0} step={0.05} value={config.p_in!} onChange={(v) => setConfig({...config, p_in: v})} disabled={isSimulating} />
          )}
          {activeParams.includes('p_out') && (
            <Slider label="P (Out)" min={0.0} max={0.2} step={0.01} value={config.p_out!} onChange={(v) => setConfig({...config, p_out: v})} disabled={isSimulating} />
          )}
        </div>
      )}

      <div style={{ marginTop: 'var(--spacing-16)' }}>
        <Button 
          variant="primary" 
          style={{ width: '100%' }} 
          onClick={executeRun} 
          isLoading={isSimulating}
        >
          {isSimulating ? 'Simulating...' : 'Run Simulation'}
        </Button>
      </div>
    </div>
  );
};
