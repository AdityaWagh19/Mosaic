import { useEffect, useState } from 'react';
import { fetchExperiments, figureUrl } from '../api/client';
import type { Experiment } from '../types/models';

const FINDINGS: Record<string, {
  figures: Record<string, { finding: string; howToRead: string }>;
}> = {
  topology: {
    figures: {
      'e1_diversity_timeseries.png': {
        finding: 'Small-world and scale-free networks converge faster than random graphs. The SBM network retains higher diversity throughout, reflecting the isolation created by sparse between-community bridges.',
        howToRead: 'Each line is one topology. The y-axis is Shannon entropy over accent-cluster membership (higher = more diverse). Runs end early when diversity stabilises; that is why lines have different lengths. A sharp drop indicates rapid convergence.',
      },
      'e1_convergence_boxplot.png': {
        finding: 'Median convergence time is shortest for BA (scale-free) networks, where hubs rapidly propagate a dominant accent. ER random graphs converge in a wider range of steps, indicating sensitivity to random tie placement.',
        howToRead: 'Each box shows the interquartile range of convergence step across multiple seeds. Whiskers extend to 1.5× IQR. Outliers above the whisker are runs that reached the maximum step limit without converging.',
      },
      'e1_final_diversity_bar.png': {
        finding: 'SBM networks end with the highest final diversity because between-community bridges are sparse enough to allow two accent groups to persist. BA networks end with the lowest diversity due to hub influence.',
        howToRead: 'Bar height is the mean final diversity across seeds. Error bars show standard deviation. A bar touching the x-axis means all agents converged to one accent cluster.',
      },
    },
  },
  prestige: {
    figures: {
      'e2_centrality_vs_influence.png': {
        finding: 'There is a positive Spearman correlation between a node\'s degree centrality and its measured influence (how much its accent shifts neighbours). The relationship is stronger at higher gamma values.',
        howToRead: 'Each point is one agent from one run. x is degree centrality (normalised 0–1); y is measured influence (number of successful accommodations toward this agent). A positive slope confirms prestige weighting works as intended.',
      },
      'e2_spearman_vs_gamma.png': {
        finding: 'As gamma increases from 0 to 2, the Spearman rank correlation between centrality and influence grows monotonically. At gamma=0 the relationship is near zero (centrality has no effect); at gamma=2 it is strong.',
        howToRead: 'x is the prestige-weight parameter gamma. y is the Spearman correlation computed across all agents and seeds at that gamma value. The shaded band is ±1 standard deviation.',
      },
      'e2_network_snapshot.png': {
        finding: 'At gamma=1.5, the final network snapshot shows hub nodes (large circles) uniformly coloured, confirming they anchor one accent cluster. Their immediate neighbours have shifted toward the hub accent.',
        howToRead: 'Node size maps to degree centrality. Node colour maps to final accent cluster (five categories). Hubs are nodes with visibly larger radius. Colour uniformity among hubs indicates accent dominance.',
      },
    },
  },
  contact: {
    figures: {
      'e3_network_4panel.png': {
        finding: 'The four panels show t=0, t=T/3, t=2T/3, and t=final. At low p_out the two communities remain visually distinct throughout. At high p_out they merge by t=T/3.',
        howToRead: 'Each panel is one timestep. Community A nodes are circular; community B nodes are square. Colour encodes accent cluster. Bridge edges (between communities) are shown as dashed lines.',
      },
      'e3_cross_community_distance.png': {
        finding: 'Cross-community accent distance drops sharply once p_out exceeds 0.05. Below this threshold, communities remain accent-distinct even at t=T_max.',
        howToRead: 'x is time (steps). y is mean pairwise accent distance between an agent in community A and an agent in community B. A drop toward zero signals community merger. Different lines are different p_out values.',
      },
      'e3_merger_time_bar.png': {
        finding: 'Merger time (first step at which cross-community distance falls below 0.05) decreases with p_out. Runs with p_out below 0.03 do not reach the merger threshold within T_max.',
        howToRead: 'Bar height is median merger time across seeds. Bars marked "No merger" hit the maximum step limit. Lower bars mean faster community merger.',
      },
    },
  },
  validation: {
    figures: {
      'ablation_boxplot.png': {
        finding: 'Removing sigma (drift) barely changes final diversity. Removing gamma (prestige) increases final diversity by approximately 15% on average, confirming prestige is the stronger convergence driver.',
        howToRead: 'Each box is one ablation condition (one parameter set to 0 while others are held fixed). The y-axis is final diversity. The baseline box is the full model. Higher boxes mean slower convergence and more accent diversity.',
      },
      'scurve.png': {
        finding: 'Accent adoption follows a logistic S-curve: slow initial spread, rapid mid-run adoption, then saturation. This matches theoretical predictions for bounded-confidence models on connected graphs.',
        howToRead: 'x is time. y is the fraction of agents whose accent has shifted more than 0.1 units toward the dominant cluster. An S-shaped curve confirms the model behaves consistently with analytic expectations.',
      },
      'heatmap_convergence_theta.png': {
        finding: 'The convergence-step heatmap shows that low theta (narrow confidence) and low sigma (low noise) together produce fast convergence. High theta with high sigma leads to persistent diversity.',
        howToRead: 'Rows are theta values; columns are sigma values. Cell colour encodes mean convergence step (darker = longer). White cells hit the maximum step limit.',
      },
      'heatmap_diversity_gamma.png': {
        finding: 'Prestige weight (gamma) and initial topology interact: in SBM networks, high gamma accelerates one community dominating the other. In ER networks, high gamma reduces diversity uniformly.',
        howToRead: 'Rows are gamma values; columns are topologies. Cell colour encodes mean final diversity. Compare across columns to isolate the topology effect at any given gamma.',
      },
    },
  },
};

const EXPERIMENT_LABELS: Record<string, string> = {
  topology: 'Topology Comparison',
  prestige: 'Prestige & Centrality',
  contact: 'Community Contact',
  validation: 'Model Validation',
};

export function ExperimentsPage({ nav }: { nav: React.ReactNode }) {
  const [items, setItems] = useState<Experiment[]>([]);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    void fetchExperiments()
      .then(data => setItems(data.items))
      .catch(cause => setError(cause.message));
  }, []);

  const displayed = filter === 'all' ? items : items.filter(i => i.id === filter);

  return (
    <main className="shell">
      {nav}
      <header className="hero" style={{ paddingBottom: 32 }}>
        <p className="eyebrow">RESEARCH ARCHIVE</p>
        <h1>Experiments, made inspectable.</h1>
        <p className="lede">
          These are completed offline experiments. Their findings are served by the API so the
          web interface never reads local project files directly. Each figure includes a short
          finding and a "How to read" guide.
        </p>
      </header>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 32, flexWrap: 'wrap' }}>
        {['all', 'topology', 'prestige', 'contact', 'validation'].map(key => (
          <button
            key={key}
            className="btn"
            style={{
              background: filter === key ? 'var(--color-ink, #000)' : 'transparent',
              color: filter === key ? '#fff' : 'var(--color-graphite)',
              border: '1px solid var(--color-hairline)',
              fontSize: 12,
              fontWeight: 600,
              padding: '6px 14px',
            }}
            onClick={() => setFilter(key)}
          >
            {key === 'all' ? 'All experiments' : EXPERIMENT_LABELS[key] ?? key}
          </button>
        ))}
      </div>

      {error ? (
        <div className="notice error">
          <strong>Could not load experiments.</strong><br />{error}
          <br /><small>Make sure the backend is running and experiment figures have been generated.</small>
        </div>
      ) : (
        <div>
          {displayed.map(item => {
            const findings = FINDINGS[item.id]?.figures ?? {};
            return (
              <section
                key={item.id}
                className="panel"
                style={{ marginBottom: 32 }}
                aria-labelledby={`exp-${item.id}-heading`}
              >
                <header style={{ marginBottom: 24 }}>
                  <p className="eyebrow">{EXPERIMENT_LABELS[item.id] ?? item.id.toUpperCase()}</p>
                  <h2 id={`exp-${item.id}-heading`} style={{ fontSize: 24, margin: '4px 0 8px' }}>
                    {item.title}
                  </h2>
                  <p className="lede" style={{ margin: 0 }}>{item.summary}</p>
                </header>

                {item.available.length === 0 ? (
                  <div className="notice">
                    No figures available yet. Run the experiment scripts to generate them:
                    <code style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                      python experiments/run_all.py
                    </code>
                  </div>
                ) : (
                  <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
                    {item.available.map(name => {
                      const meta = findings[name];
                      const caption = name.replace(/_/g, ' ').replace('.png', '');
                      return (
                        <figure key={name} style={{ margin: 0 }}>
                          <div
                            className="card"
                            style={{ padding: 0, overflow: 'hidden', position: 'relative' }}
                          >
                            <img
                              src={figureUrl(name)}
                              alt={`${item.title}: ${caption}`}
                              style={{ display: 'block', width: '100%' }}
                              onError={e => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                            {/* Download button */}
                            <a
                              href={figureUrl(name)}
                              download={name}
                              aria-label={`Download ${caption}`}
                              style={{
                                position: 'absolute',
                                top: 8,
                                right: 8,
                                background: 'rgba(255,255,255,0.9)',
                                border: '1px solid var(--color-hairline)',
                                borderRadius: 8,
                                padding: '4px 10px',
                                fontSize: 11,
                                fontWeight: 600,
                                textDecoration: 'none',
                                color: 'var(--color-graphite)',
                              }}
                            >
                              ↓ PNG
                            </a>
                          </div>
                          <figcaption style={{ padding: '12px 0 0' }}>
                            <p style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>
                              {caption}
                            </p>
                            {meta && (
                              <>
                                <p style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--color-graphite)', lineHeight: 1.5 }}>
                                  {meta.finding}
                                </p>
                                <details>
                                  <summary style={{ fontSize: 12, color: 'var(--color-ash)', cursor: 'pointer', userSelect: 'none' }}>
                                    How to read this figure
                                  </summary>
                                  <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--color-graphite)', lineHeight: 1.5 }}>
                                    {meta.howToRead}
                                  </p>
                                </details>
                              </>
                            )}
                          </figcaption>
                        </figure>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </main>
  );
}
