import { Link } from 'react-router-dom';
import { BlurReveal } from '../components/ui/motion/BlurReveal';
import { IllSpeaker, IllInfluence, IllNetwork, IllMetrics, IllLimits } from '../components/ui/IllustrationGuide';

export function GuidePage({ nav }: { nav?: React.ReactNode }) {
  const sections = [
    { title: 'What is a speaker?', copy: 'A speaker is an agent with six synthetic accent features. Mosaic does not represent recorded voices, real people, or demographic groups.', Ill: IllSpeaker },
    { title: 'How do speakers influence one another?', copy: 'At each step, a connected pair may accommodate when their accents are close enough. Prestige can weight the influence of highly connected speakers.', Ill: IllInfluence },
    { title: 'How does the network matter?', copy: 'The network determines who can meet. Random, clustered, hub-dominated, and two-community structures expose different paths for accent change.', Ill: IllNetwork },
    { title: 'What do the metrics mean?', copy: 'Diversity describes how accent clusters are distributed. Pairwise distance describes average separation between speaker accent vectors. Consensus means every speaker accent is within the model tolerance of every other.', Ill: IllMetrics },
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
          <article key={title} className="guide-section">
            <div className="guide-timeline">
              <span className="guide-number">0{index + 1}</span>
              {index < sections.length - 1 && <div className="guide-line" />}
            </div>
            <div className="guide-ill-wrapper">
              <Ill />
            </div>
            <div className="guide-content">
              <h2>{title}</h2>
              <p>{copy}</p>
              {index === 1 && <div><Link className="btn btn-secondary" to="/simulate">Try the small-world baseline →</Link></div>}
              {index === 2 && <div><Link className="btn btn-secondary" to="/simulate">Try two-community contact →</Link></div>}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
