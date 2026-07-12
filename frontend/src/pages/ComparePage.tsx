import { useEffect, useMemo, useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { fetchResult, fetchRuns } from '../api/client';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { BlurReveal } from '../components/ui/motion/BlurReveal';
import { LineReveal } from '../components/ui/motion/LineReveal';
import { IllustrationCompare } from '../components/ui/IllustrationCompare';
import type { RunResponse, RunSummary } from '../types/models';

const colors = ['#0077ff', '#000000', '#f97316', '#2563eb']; 
const fields = ['topology', 'N', 'T', 'gamma', 'theta', 'sigma', 'seed'] as const;

export function ComparePage({ nav }: { nav: React.ReactNode }) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [results, setResults] = useState<RunResponse[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [differencesOnly, setDifferencesOnly] = useState(false);
  const [normalized, setNormalized] = useState(false);

  useEffect(() => { 
    void fetchRuns()
      .then(data => setRuns(data.items))
      .catch(cause => setError(cause.message))
      .finally(() => setLoading(false)); 
  }, []);

  useEffect(() => { 
    void Promise.all(selected.map(fetchResult))
      .then(setResults)
      .catch(cause => setError(cause.message)); 
  }, [selected]);

  const toggle = (id: string) => {
    setSelected(current => {
      if (current.includes(id)) {
        return current.filter(value => value !== id);
      }
      if (current.length < 4) {
        return [...current, id];
      }
      return current;
    });
  };

  const chart = useMemo(() => { 
    const points = new Map<number, Record<string, number>>(); 
    results.forEach(result => { 
      const end = result.timeline.at(-1)?.timestep || 1; 
      result.timeline.forEach(point => { 
        const step = normalized ? Math.round(point.timestep / end * 100) : point.timestep; 
        points.set(step, { ...(points.get(step) ?? {}), timestep: step, [result.run_id]: point.diversity }); 
      }); 
    }); 
    return [...points.values()].sort((a, b) => a.timestep - b.timestep); 
  }, [results, normalized]);

  const changed = (field: typeof fields[number]) => new Set(results.map(result => String(result.config[field]))).size > 1; 
  const shown = fields.filter(field => !differencesOnly || changed(field)); 
  const differenceCount = fields.filter(changed).length; 
  const controlled = differenceCount === 1; 
  const incompatible = new Set(results.map(r => r.timeline.at(-1)?.timestep)).size > 1;

  return (
    <main className="shell">
      {nav}
      <header className="hero compact-hero">
        <p className="eyebrow">RUN COMPARISON</p>
        <BlurReveal as="h1">Compare completed runs.</BlurReveal>
        <p className="lede">Choose two to four runs. Mosaic identifies whether the configurations isolate one changed assumption or mix several changes.</p>
      </header>
      
      {error ? (
        <div className="notice error" role="alert">
          <strong>Could not load the run archive.</strong>
          <p>{error}</p>
        </div>
      ) : loading ? (
        <section className="section">
          <LoadingSkeleton />
          <div style={{ height: 16 }} />
          <LoadingSkeleton chart />
        </section>
      ) : (
        <>
          <section className="panel">
            <div className="section-head">
              <div>
                <h2 className="panel-title">Run archive</h2>
                <p className="panel-description">Select up to four completed configurations.</p>
              </div>
              <span className="selection-count">{selected.length}/4 selected</span>
            </div>
            <div className="run-archive">
              {runs.map(run => (
                <label key={run.run_id} className={selected.includes(run.run_id) ? 'is-selected' : ''}>
                  <input type="checkbox" checked={selected.includes(run.run_id)} onChange={() => toggle(run.run_id)} disabled={!selected.includes(run.run_id) && selected.length >= 4} />
                  <span>
                    <strong>{run.run_id}</strong>
                    <small>{run.topology} · seed {run.seed} · final H {run.final_diversity?.toFixed(3)}</small>
                  </span>
                </label>
              ))}
            </div>
          </section>

          <LineReveal className="section-divider" style={{ marginTop: 0 }} />
          <section className="section">
            <div className="section-head">
              <div>
                <BlurReveal as="h2">Comparison evidence</BlurReveal>
                <p className="lede">Read configuration differences before interpreting outcome differences.</p>
              </div>
              {results.length >= 2 && (
                <div className="switches">
                  <label className="switch">
                    <input type="checkbox" checked={differencesOnly} onChange={event => setDifferencesOnly(event.target.checked)} /> Only show differences
                  </label>
                  {incompatible && (
                    <label className="switch">
                      <input type="checkbox" checked={normalized} onChange={event => setNormalized(event.target.checked)} /> Normalize timeline
                    </label>
                  )}
                </div>
              )}
            </div>

            {results.length < 2 ? (
              <div className="empty-state compare-empty">
                <IllustrationCompare />
                <p>Select two to four runs from the archive to compare their configurations and outcomes.</p>
              </div>
            ) : (
              <>
                <div className={`comparison-status ${controlled ? 'controlled' : 'mixed'}`}>
                  <strong>{controlled ? 'Controlled comparison' : 'Mixed comparison'}</strong>
                  <p>
                    {controlled 
                      ? `Only ${fields.find(changed)?.replace('_', ' ')} differs, so the trajectory comparison isolates one configured assumption.` 
                      : `These runs differ in ${differenceCount} ways. Inspect each parameter change before drawing conclusions.`
                    }
                  </p>
                </div>

                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Parameter</th>
                        {results.map(result => <th key={result.run_id}>{result.run_id}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {shown.map(field => (
                        <tr key={field} className={changed(field) ? 'changed-row' : ''}>
                          <td>{field.replace(/_/g, ' ')}</td>
                          {results.map(result => (
                            <td key={result.run_id}>{String(result.config[field])}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="panel chart comparison-chart">
                  <h3 className="panel-title">Diversity trajectory</h3>
                  <p className="panel-description">
                    {normalized ? 'Aligned to each run’s completion point (0–100%).' : 'Aligned by simulation step. Lines may end at different points when runs converge early.'}
                  </p>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chart} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                      <CartesianGrid stroke="#e5e7eb" vertical={false} />
                      <XAxis dataKey="timestep" label={normalized ? { value: 'Progress (%)', position: 'insideBottom', offset: -10 } : undefined} />
                      <YAxis label={{ value: 'Diversity (H)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip contentStyle={{ border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 12 }} />
                      <Legend verticalAlign="top" height={36} />
                      {results.map((result, index) => (
                        <Line key={result.run_id} dataKey={result.run_id} stroke={colors[index]} dot={false} strokeWidth={2} name={result.run_id} />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </section>
        </>
      )}
    </main>
  );
}
