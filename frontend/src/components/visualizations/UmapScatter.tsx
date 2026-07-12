import { useMemo, useRef, useState } from 'react';
import { useD3Scatter } from '../../hooks/useD3Scatter';
import { useResizeObserver } from '../../hooks/useResizeObserver';
import type { AgentState, UmapResponse } from '../../types/models';

function stageName(index: number, total: number) { if (index === 0) return 'Initial state'; if (index === total - 1) return 'Final state'; if (index <= Math.floor((total - 1) / 2)) return 'Early interaction'; return 'Mid-run'; }
export function UmapScatter({ data, agentStates }: { data: UmapResponse | null; agentStates: AgentState[] }) {
  const [index, setIndex] = useState(0); const container = useRef<HTMLDivElement>(null); const { width, height } = useResizeObserver(container);
  const snapshot = data?.snapshots[Math.min(index, (data?.snapshots.length ?? 1) - 1)];
  const orderedStates = useMemo(() => snapshot ? snapshot.points.map(point => agentStates.find(agent => agent.agent_id === point.agent_id) ?? { agent_id: point.agent_id, community_id: point.community_id, centrality: 0, cluster_id: 0, accent: [] }) : [], [snapshot, agentStates]);
  const svg = useD3Scatter({ coords: snapshot?.points.map(point => [point.x, point.y] as [number, number]) ?? [], agentStates: orderedStates, width, height });
  if (!data) return <div className="notice">Preparing the accent-space projection. The rest of this result is available now.</div>;
  return <><div className="stage-header"><div><p className="eyebrow">ACCENT EVOLUTION</p><h3>{stageName(index, data.snapshots.length)}</h3><p>Step {snapshot?.timestep ?? 0}. Nearby points have more similar synthetic accents; this is not a geographic map.</p></div></div><div className="stage-selector" aria-label="Accent evolution stages">{data.snapshots.map((item, itemIndex) => <button key={item.timestep} aria-pressed={index === itemIndex} onClick={() => setIndex(itemIndex)}>{stageName(itemIndex, data.snapshots.length)}<span>t = {item.timestep}</span></button>)}</div><div className="viz" ref={container} style={{ marginTop: 16, border: '1px solid var(--color-hairline)', borderRadius: 'var(--radius-cards)', overflow: 'hidden' }}><svg ref={svg} width="100%" height="100%" role="img" aria-label={`Accent space projection at step ${snapshot?.timestep ?? 0}`}><title>Accent space UMAP projection</title><desc>A two-dimensional projection of six-dimensional synthetic accent vectors.</desc></svg></div></>;
}
