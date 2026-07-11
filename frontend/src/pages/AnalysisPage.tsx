import { useEffect, useState } from 'react';
import { fetchAnalysis, figureUrl } from '../api/client';
import type { AnalysisSummary } from '../types/models';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';

interface MetricCardProps { label: string; value: string; sub?: string; highlight?: boolean }
function MetricCard({ label, value, sub, highlight }: MetricCardProps) {
  return (
    <div
      className="metric"
      style={{ borderTop: highlight ? '2px solid var(--color-signal-blue)' : undefined }}
    >
      <span>{label}</span>
      <strong style={{ fontSize: 28 }}>{value}</strong>
      {sub && <small style={{ display: 'block', fontSize: 11, opacity: 0.7, marginTop: 2 }}>{sub}</small>}
    </div>
  );
}

export function AnalysisPage({ nav }: { nav: React.ReactNode }) {
  const [data, setData] = useState<AnalysisSummary | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    void fetchAnalysis()
      .then(setData)
      .catch(cause => setError(cause.message));
  }, []);

  return (
    <main className="shell">
      {nav}
      <header className="hero" style={{ paddingBottom: 32 }}>
        <p className="eyebrow">OFFLINE ML BENCHMARK</p>
        <h1>What the model learned.</h1>
        <p className="lede">
          These are benchmark results from completed offline simulation runs, not real-time
          predictions for a newly created run. Results are pre-computed and served by the API.
        </p>
      </header>

      {error ? (
        <div className="notice error">
          <strong>Could not load analysis results.</strong><br />{error}
          <br /><small>Make sure the backend is running and <code>results/ml_results.json</code> exists.</small>
        </div>
      ) : !data ? (
        <section className="section"><span className="spinner" aria-label="Loading analysis" /><LoadingSkeleton chart /><div style={{ height: 16 }} /><LoadingSkeleton /></section>
      ) : (
        <>
          <section className="result-statement" aria-labelledby="ml-conclusion"><span className="result-statement-label">Plain-language conclusion</span><div><h2 id="ml-conclusion" className="panel-title">Initial accent features were more predictive than the tested graph representation.</h2><p>The MLP outperformed the tested GCN on this synthetic benchmark. This is a benchmark result, not evidence about real-world accent change.</p></div></section>
          <section className="panel" style={{ marginBottom: 32 }}><h2 className="panel-title">Question and scope</h2><p className="panel-description">Can initial speaker features and social-network structure predict a speaker’s final k-means cluster? The target is a post-hoc partition of simulated accent vectors, so it is a useful diagnostic rather than a discovered dialect label.</p></section>
          {/* ── Benchmark summary cards ─────────────────────────────── */}
          <section aria-labelledby="benchmark-heading" style={{ marginBottom: 48 }}>
            <h2 id="benchmark-heading" style={{ fontSize: 20, marginBottom: 16 }}>
              Model benchmarks
            </h2>
            <div className="metrics" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10 }}>
              <MetricCard label="MLP accuracy" value={`${(data.mlp.accuracy * 100).toFixed(2)}%`} sub={`Macro-F1: ${(data.mlp.macro_f1 * 100).toFixed(2)}%`} highlight />
              <MetricCard label="GCN accuracy" value={`${(data.gcn.accuracy * 100).toFixed(2)}%`} sub={`Macro-F1: ${(data.gcn.macro_f1 * 100).toFixed(2)}%`} />
              <MetricCard label="Random chance" value={`${(data.random_chance * 100).toFixed(0)}%`} sub="5 classes" />
              <MetricCard label="Training runs" value={String(data.n_train_runs ?? '80')} />
              <MetricCard label="Test runs" value={String(data.n_test_runs)} />
              <MetricCard label="Target clusters" value="5" sub="k-means, k=5" />
            </div>
          </section>

          {/* ── Benchmark table ─────────────────────────────────────── */}
          <section aria-labelledby="table-heading" style={{ marginBottom: 48 }}>
            <h2 id="table-heading" style={{ fontSize: 20, marginBottom: 16 }}>
              Detailed comparison table
            </h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--color-hairline)' }}>
                    {['Model', 'Accuracy', 'Macro-F1', 'vs Random chance', 'Notes'].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontSize: 11, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--color-ash)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      name: 'MLP (baseline)',
                      acc: data.mlp.accuracy,
                      f1: data.mlp.macro_f1,
                      notes: 'Uses only initial node features (accent vectors). Outperformed GCN.',
                    },
                    {
                      name: 'GCN',
                      acc: data.gcn.accuracy,
                      f1: data.gcn.macro_f1,
                      notes: 'Graph convolutional network. Underperformed MLP on this synthetic dataset.',
                    },
                    {
                      name: 'Random chance',
                      acc: data.random_chance,
                      f1: data.random_chance,
                      notes: 'Uniform random class assignment. Lower bound.',
                    },
                  ].map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--color-hairline)', background: i === 0 ? 'rgba(0,0,0,0.02)' : undefined }}>
                      <td style={{ padding: '10px 12px', fontWeight: i < 2 ? 600 : 400 }}>{row.name}</td>
                      <td style={{ padding: '10px 12px', fontVariantNumeric: 'tabular-nums' }}>{(row.acc * 100).toFixed(2)}%</td>
                      <td style={{ padding: '10px 12px', fontVariantNumeric: 'tabular-nums' }}>{(row.f1 * 100).toFixed(2)}%</td>
                      <td style={{ padding: '10px 12px', color: 'var(--color-graphite)', fontVariantNumeric: 'tabular-nums' }}>
                        {i === 2 ? '—' : `+${((row.acc - data.random_chance) * 100).toFixed(1)} pp`}
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--color-graphite)', fontSize: 12 }}>{row.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ── Clustering diagnostics ──────────────────────────────── */}
          <section aria-labelledby="clustering-heading" style={{ marginBottom: 48 }}>
            <h2 id="clustering-heading" style={{ fontSize: 20, marginBottom: 8 }}>
              Clustering diagnostics
            </h2>
            <p className="lede" style={{ margin: '0 0 24px' }}>
              Cluster quality was assessed using two methods after the simulation.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16, marginBottom: 24 }}>
              <div className="card">
                <h3 style={{ margin: '0 0 4px', fontSize: 14 }}>k-means silhouette</h3>
                <p style={{ margin: '0 0 8px', fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em' }}>
                  {data.clustering.kmeans_silhouette.toFixed(4)}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--color-graphite)', lineHeight: 1.4 }}>
                  Silhouette scores near 0 indicate overlapping clusters, meaning agents' final accent vectors do not form naturally separated groups.
                  This is a result, not a failure — the accommodation model often produces gradient distributions rather than discrete dialect zones.
                </p>
              </div>
              <div className="card">
                <h3 style={{ margin: '0 0 4px', fontSize: 14 }}>DBSCAN clusters found</h3>
                <p style={{ margin: '0 0 8px', fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em' }}>
                  {data.clustering.dbscan_n_clusters}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--color-graphite)', lineHeight: 1.4 }}>
                  DBSCAN found {data.clustering.dbscan_n_clusters === 1 ? 'only one dense cluster' : `${data.clustering.dbscan_n_clusters} clusters`},
                  suggesting the accent space does not have multiple well-separated, high-density regions.
                  The five k-means groups are a fixed-k partition, not naturally discovered dialect boundaries.
                </p>
              </div>
            </div>
          </section>

          {/* ── Honest interpretation ───────────────────────────────── */}
          <section className="panel" style={{ marginBottom: 48, borderLeft: '3px solid var(--color-hairline)' }}>
            <h2 style={{ fontSize: 18, marginBottom: 12 }}>Interpretation</h2>
            <p className="lede" style={{ margin: '0 0 12px' }}>
              The MLP (using only initial node features) outperformed the GCN (using graph structure).
              This is evidence that on this synthetic dataset, initial accent-vector proximity is
              more informative than network topology for predicting final cluster membership.
            </p>
            <p className="lede" style={{ margin: '0 0 12px' }}>
              <strong>This is not a general claim about real-world accent change.</strong> The dataset
              is fully synthetic, the network sizes are small (80 training runs), and the clusters
              are imposed by k-means post-hoc, not observed empirically.
            </p>
            <p className="lede" style={{ margin: 0 }}>
              The near-zero silhouette and single DBSCAN cluster are the most honest finding:
              well-separated dialect zones were not discovered in this benchmark. That reflects the
              model's accommodation dynamics, not a classification error.
            </p>
          </section>

          {/* ── Figures ─────────────────────────────────────────────── */}
          {data.figures.length > 0 && (
            <section aria-labelledby="figures-heading" style={{ marginBottom: 48 }}>
              <h2 id="figures-heading" style={{ fontSize: 20, marginBottom: 16 }}>Generated figures</h2>
              <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 20 }}>
                {data.figures.map(name => (
                  <figure key={name} style={{ margin: 0 }}>
                    <div className="card" style={{ padding: 0, overflow: 'hidden', position: 'relative' }}>
                      <img
                        src={figureUrl(name)}
                        alt={name.replace(/_/g, ' ').replace('.png', '')}
                        style={{ display: 'block', width: '100%' }}
                      />
                      <a
                        href={figureUrl(name)}
                        download={name}
                        style={{
                          position: 'absolute', top: 8, right: 8,
                          background: 'rgba(255,255,255,0.9)',
                          border: '1px solid var(--color-hairline)',
                          borderRadius: 8, padding: '4px 10px',
                          fontSize: 11, fontWeight: 600, textDecoration: 'none',
                          color: 'var(--color-graphite)',
                        }}
                      >
                        ↓ PNG
                      </a>
                    </div>
                    <figcaption style={{ marginTop: 8, fontSize: 12, color: 'var(--color-graphite)' }}>
                      {name.replace(/_/g, ' ').replace('.png', '')}
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}
