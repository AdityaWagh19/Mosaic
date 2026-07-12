import { Link } from 'react-router-dom';
import { BlurReveal } from '../components/ui/motion/BlurReveal';
import { IllSpeaker, IllInfluence, IllNetwork, IllMetrics, IllLimits } from '../components/ui/IllustrationGuide';

export function GuidePage({ nav }: { nav?: React.ReactNode }) {
  const sections = [
    { title: 'What is a speaker?', copy: 'A speaker is an agent with six synthetic accent features. Mosaic does not represent recorded voices, real people, or demographic groups.', Ill: IllSpeaker },
    { title: 'How do speakers influence one another?', copy: 'At each step, a connected pair may accommodate when their accents are close enough. Prestige can weight the influence of highly connected speakers.', Ill: IllInfluence },
    { title: 'How does the network matter?', copy: 'The network determines who can meet. Random, clustered, hub-dominated, and two-community structures expose different paths for accent change.', Ill: IllNetwork },
    { title: 'What do the metrics mean?', copy: 'Diversity describes how accent clusters are distributed. Pairwise distance describes average separation between speaker accent vectors. Convergence means diversity stabilized.', Ill: IllMetrics },
    { title: 'What Mosaic does not model', copy: 'Mosaic is a conceptual agent-based model. It does not make claims about real speech communities, identity, geography, or causal mechanisms outside its explicit rules.', Ill: IllLimits },
  ];

  return (
    <main className="shell">
      {nav && <section>{nav}</section>}
      <section className="hero compact-hero">
        <p className="eyebrow">METHOD GUIDE</p>
        <BlurReveal as="h1">From social ties to accent patterns.</BlurReveal>
        <p className="lede">A short guide to the model, its evidence, and its limits.</p>
      </section>
      <section className="method-guide">
        {sections.map(({ title, copy, Ill }, index) => (
          <article key={title} className="guide-section" style={{ border: '1px solid var(--color-hairline)', padding: 24, borderRadius: 'var(--radius-cards)', marginBottom: 24, background: 'var(--color-paper)' }}>
            <Ill />
            <h2 style={{ fontSize: 20, marginTop: 16, marginBottom: 8 }}>{title}</h2>
            <p style={{ margin: 0, color: 'var(--color-graphite)', fontSize: 15 }}>{copy}</p>
            {index === 1 && <div style={{ marginTop: 16 }}><Link className="btn btn-secondary" to="/simulate">Try the small-world baseline →</Link></div>}
            {index === 2 && <div style={{ marginTop: 16 }}><Link className="btn btn-secondary" to="/simulate">Try two-community contact →</Link></div>}
          </article>
        ))}
      </section>
    </main>
  );
}
