import { useCallback, useRef, useState } from 'react';
import { useD3Network } from '../../hooks/useD3Network';
import { useResizeObserver } from '../../hooks/useResizeObserver';
import type { AgentState, NetworkEdge, NetworkNode } from '../../types/models';

export function NetworkGraph({ nodes, edges, agentStates }: { nodes: NetworkNode[]; edges: NetworkEdge[]; agentStates: AgentState[] }) {
  const container = useRef<HTMLDivElement>(null); const { width, height } = useResizeObserver(container);
  const [selectedId, setSelectedId] = useState<number | null>(null); const [showLabels, setShowLabels] = useState(false); const [resetKey, setResetKey] = useState(0);
  const select = useCallback((agentId: number) => setSelectedId(agentId), []);
  const svg = useD3Network({ nodes, edges, agentStates, width, height, onSelect: select, showLabels });
  const selected = agentStates.find(agent => agent.agent_id === selectedId);
  return <>
    <div className="viz-toolbar"><div className="viz-legend"><span><i className="legend-dot cluster-0" /> Accent cluster</span><span><i className="legend-size" /> Node size: centrality</span><span><i className="legend-line" /> Tie: possible interaction</span></div><div className="actions"><button className="btn btn-secondary" onClick={() => setShowLabels(value => !value)}>{showLabels ? 'Hide labels' : 'Show labels'}</button><button className="btn btn-secondary" onClick={() => { setSelectedId(null); setResetKey(value => value + 1); }}>Reset view</button></div></div>
    <div className="network-layout"><div className="viz" ref={container} style={{ border: '1px solid var(--color-hairline)', borderRadius: 'var(--radius-cards)', overflow: 'hidden' }}><svg key={resetKey} ref={svg} width="100%" height="100%" role="img" aria-label="Interactive final network graph"><title>Final social network graph</title><desc>Select a speaker to inspect its community, centrality, cluster, and accent dimensions.</desc></svg></div>
      <aside className="agent-inspector" aria-live="polite"><p className="eyebrow">SPEAKER INSPECTOR</p>{selected ? <><h3>Speaker {selected.agent_id}</h3><dl><div><dt>Community</dt><dd>{selected.community_id}</dd></div><div><dt>Accent cluster</dt><dd>{selected.cluster_id}</dd></div><div><dt>Centrality</dt><dd>{selected.centrality.toFixed(3)}</dd></div></dl><p className="inspector-label">Accent dimensions</p><div className="accent-dimensions">{selected.accent.map((value, index) => <span key={index}>d{index}: {value.toFixed(3)}</span>)}</div></> : <p>Select a speaker in the graph or use the data table to inspect its state.</p>}</aside></div>
    <details><summary>Open the accessible speaker data table</summary><div className="table-wrap"><table><thead><tr><th>Speaker</th><th>Community</th><th>Cluster</th><th>Centrality</th><th>Inspect</th></tr></thead><tbody>{agentStates.map(agent => <tr key={agent.agent_id}><td>{agent.agent_id}</td><td>{agent.community_id}</td><td>{agent.cluster_id}</td><td>{agent.centrality.toFixed(3)}</td><td><button className="table-action" onClick={() => setSelectedId(agent.agent_id)}>Inspect</button></td></tr>)}</tbody></table></div></details>
  </>;
}
