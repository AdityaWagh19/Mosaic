import * as Tabs from '@radix-ui/react-tabs';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ControlPanel } from '../components/simulation/ControlPanel';
import { NetworkGraph } from '../components/visualizations/NetworkGraph';
import { SnapshotPlayback } from '../components/visualizations/SnapshotPlayback';
import { TimeSeriesChart } from '../components/visualizations/TimeSeriesChart';
import { UmapScatter } from '../components/visualizations/UmapScatter';
import { exportUrl } from '../api/client';
import { useSimulation } from '../contexts/SimulationContext';
import { InfoTooltip } from '../components/ui/InfoTooltip';
import { useToast } from '../components/ui/ToastProvider';
import { AnimatedNumber } from '../components/ui/AnimatedNumber';
import { StaggerFade } from '../components/ui/motion/StaggerFade';
import { PDFDownloadLink } from '@react-pdf/renderer';
import { ReportPDF } from '../components/ui/ReportPDF';
import type { RunResponse, SimConfig } from '../types/models';
import { PRESETS } from '../constants/presets';
import { Network, Share2, Users, Focus, Waypoints, ScatterChart } from 'lucide-react';

const ICONS = { Network, Share2, Users, Focus };

type Tab = 'overview' | 'network' | 'accent' | 'data';
export function Dashboard({ nav }: { nav: React.ReactNode }) {
  const { runId } = useParams(); const navigate = useNavigate(); const [params, setParams] = useSearchParams(); const { notify } = useToast();
  const { result, umap, error, isRunning, run, load, clear, setConfig } = useSimulation(); const tab = (params.get('tab') as Tab) || 'overview'; const [activeTab, setActiveTab] = useState<Tab>(tab);
  const resultHeadingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (runId) void load(runId); else clear(); }, [runId, load, clear]);
  useEffect(() => { if (result) { resultHeadingRef.current?.focus(); } }, [result]);
  const copy = async () => { if (result) { await navigator.clipboard?.writeText(`${window.location.origin}/runs/${result.run_id}`); notify('Run link copied to clipboard.'); } };
  return <main className="shell">{nav}<div className="studio"><ControlPanel /><section aria-live="polite">{error ? <div className="notice error" role="alert"><strong>This run could not be completed.</strong><p>{error}</p><button className="btn btn-secondary" onClick={() => void run()}>Try again</button></div> : isRunning ? <SimulationLoading /> : !result ? <EmptyState /> : <>
    <header className="run-header"><div><p className="eyebrow">COMPLETED RUN</p><h1 ref={resultHeadingRef} tabIndex={-1} style={{ outline: 'none' }}>{result.metrics.converged ? 'Diversity stabilized' : 'Maximum interactions reached'}</h1><p>Run {result.run_id}</p></div><div className="actions">
      <PDFDownloadLink document={<ReportPDF result={result} />} fileName={`mosaic-run-${result.run_id}.pdf`} className="btn btn-secondary">
        {({ loading }) => (loading ? 'Generating PDF...' : 'Download PDF')}
      </PDFDownloadLink>
      <button className="btn btn-secondary" onClick={() => void copy()}>Copy run link</button><button className="btn btn-secondary" onClick={() => { setConfig(result.config); navigate('/simulate'); }}>Use this configuration</button></div></header>
    <div className="result-statement"><span className="result-statement-label">Run interpretation</span><p>{interpretRun(result)}</p></div>
    <div className="metrics"><StaggerFade stagger={0.06}><Metric label="Run status" value={result.metrics.converged ? 'Converged' : 'Maximum reached'} help="Whether diversity stabilized before the configured interaction limit." /><Metric label="Convergence time" value={result.metrics.converged ? `${result.metrics.convergence_time} steps` : 'Not reached'} number={result.metrics.converged ? result.metrics.convergence_time : undefined} help="The first step at which the convergence criterion was met." /><Metric label="Final diversity" value={`H = ${result.metrics.final_diversity.toFixed(3)}`} number={result.metrics.final_diversity} help="How evenly final accent clusters are represented." /><Metric label="Pairwise distance" value={`D = ${result.metrics.final_pairwise_distance.toFixed(3)}`} number={result.metrics.final_pairwise_distance} help="Average separation among synthetic accent vectors." /></StaggerFade></div>
    <Tabs.Root className="result-tabs" value={activeTab} onValueChange={value => { setActiveTab(value as Tab); setParams({ tab: value }); }}><Tabs.List className="tabs" aria-label="Result views">{(['overview', 'network', 'accent', 'data'] as Tab[]).map(item => <Tabs.Trigger key={item} className="tab" value={item} onClick={() => { setActiveTab(item); setParams({ tab: item }); }}>{item === 'accent' ? 'Accent space' : item[0].toUpperCase() + item.slice(1)}</Tabs.Trigger>)}</Tabs.List><Tabs.Content value="overview" className="panel"><h2 className="panel-title">Evidence over time</h2><p className="panel-description">Diversity tracks accent-cluster distribution. Pairwise distance is the average separation between six-dimensional accent vectors.</p><TimeSeriesChart data={result.timeline} /><div className="overview-previews"><button onClick={() => { setActiveTab('network'); setParams({ tab: 'network' }); }}><span className="preview-network" aria-hidden="true"><Waypoints size={18} /></span><strong>Social network</strong><small>{result.network.nodes.length} speakers · {result.network.edges.length} ties</small></button><button onClick={() => { setActiveTab('accent'); setParams({ tab: 'accent' }); }}><span className="preview-points" aria-hidden="true"><ScatterChart size={18} /></span><strong>Accent evolution</strong><small>{umap?.snapshots.length ?? 0} observed stages</small></button></div><details><summary>How to interpret this run</summary><p>Read the trajectory first, then compare possible social interactions with the final accent-space projection.</p></details><details><summary>Open the time-series data table</summary><table><thead><tr><th>Step</th><th>Diversity</th><th>Pairwise distance</th></tr></thead><tbody>{result.timeline.map(point => <tr key={point.timestep}><td>{point.timestep}</td><td>{point.diversity.toFixed(4)}</td><td>{point.pairwise_distance.toFixed(4)}</td></tr>)}</tbody></table></details></Tabs.Content><Tabs.Content value="network" className="panel"><h2 className="panel-title">Who can influence whom</h2><p className="panel-description">Nodes are speakers; ties are possible interactions. Use the graph to relate structure to the final accent pattern.</p><NetworkGraph nodes={result.network.nodes} edges={result.network.edges} agentStates={result.final_agent_states} /></Tabs.Content><Tabs.Content value="accent" className="panel"><h2 className="panel-title">How accents group in space</h2><p className="panel-description">This projection preserves broad similarity: nearby points have more similar synthetic accents.</p><UmapScatter data={umap} agentStates={result.final_agent_states} /></Tabs.Content><Tabs.Content value="data" className="panel"><h2 className="panel-title">Reproducibility details</h2><p className="panel-description">Use the same configuration and seed to reproduce this model run.</p><div className="actions"><a className="btn btn-primary" href={exportUrl(result.run_id, 'json')}>Download JSON</a><a className="btn btn-secondary" href={exportUrl(result.run_id, 'csv')}>Download agent CSV</a></div><div className="data-list">{Object.entries(result.config).filter(([key]) => key !== 'run_id').map(([key, value]) => <div key={key}><span>{key.replace(/_/g, ' ')}</span>{String(value)}</div>)}</div><SnapshotPlayback runId={result.run_id} /></Tabs.Content></Tabs.Root>
  </>}</section></div></main>;
}
function Metric({ label, value, number, help }: { label: string; value: string; number?: number; help: string }) { const output = label === 'Convergence time' ? (n: number) => `${Math.round(n)} steps` : label === 'Final diversity' ? (n: number) => `H = ${n.toFixed(3)}` : (n: number) => `D = ${n.toFixed(3)}`; return <div className="metric"><span>{label} <InfoTooltip label={help} /></span><strong>{number === undefined ? value : <AnimatedNumber value={number} format={output} />}</strong></div>; }
function EmptyState() { 
  const { config, setConfig, run } = useSimulation();
  
  return (
    <div className="empty empty-start">
      <div style={{ width: '100%' }}>
        <p className="eyebrow">SIMULATION STUDIO</p>
        <h2>Start with a question.</h2>
        <p>Choose a preset to explore a known pattern, or configure a network from first principles.</p>
        <div className="preset-cards">
          {Object.values(PRESETS).map(preset => {
            const Icon = ICONS[preset.icon];
            return (
              <button 
                key={preset.name} 
                className="preset-card" 
                onClick={() => { setConfig({...config, ...preset.config} as SimConfig); setTimeout(() => run(), 50); }}
              >
                <div className="preset-icon"><Icon size={20} /></div>
                <h3>{preset.name}</h3>
                <p>{preset.desc}</p>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  ); 
}
function SimulationLoading() { return <div className="empty loading-state" aria-live="polite"><div><span className="spinner" /><p className="eyebrow">SIMULATION IN PROGRESS</p><h2>Building your result.</h2><p>The model is preparing the network, simulating speaker interactions, and assembling the visual evidence.</p><ol className="loading-steps"><li className="is-active">Build the social network</li><li>Simulate local influence</li><li>Prepare graphs and projections</li></ol></div></div>; }
function interpretRun(result: RunResponse) { const { metrics } = result; return metrics.converged ? `The population reached a stable state after ${metrics.convergence_time} steps. Final diversity was ${metrics.final_diversity.toFixed(3)}, indicating how evenly accent clusters remained represented.` : `The population was still changing when the ${result.config.T.toLocaleString()}-step limit was reached. Final diversity was ${metrics.final_diversity.toFixed(3)}; inspect the trajectory to see whether groups were still separating or moving together.`; }
