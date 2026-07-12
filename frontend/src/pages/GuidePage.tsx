import { Link } from 'react-router-dom';

export function GuidePage({ nav }: { nav?: React.ReactNode }) {
  const sections = [
    ['What is a speaker?', 'A speaker is an agent with six synthetic accent features. Mosaic does not represent recorded voices, real people, or demographic groups.'],
    ['How do speakers influence one another?', 'At each step, a connected pair may accommodate when their accents are close enough. Prestige can weight the influence of highly connected speakers.'],
    ['How does the network matter?', 'The network determines who can meet. Random, clustered, hub-dominated, and two-community structures expose different paths for accent change.'],
    ['What do the metrics mean?', 'Diversity describes how accent clusters are distributed. Pairwise distance describes average separation between speaker accent vectors. Convergence means diversity stabilized.'],
    ['What Mosaic does not model', 'Mosaic is a conceptual agent-based model. It does not make claims about real speech communities, identity, geography, or causal mechanisms outside its explicit rules.'],
  ];

  return (
    <main className="shell">
      {nav && <section>{nav}</section>}
      <section className="hero compact-hero">
        <p className="eyebrow">METHOD GUIDE</p>
        <h1>From social ties to accent patterns.</h1>
        <p className="lede">A short guide to the model, its evidence, and its limits.</p>
      </section>
      <section className="method-guide">
        {sections.map(([title, copy], index) => (
          <details key={title} open={index === 0}>
            <summary>{title}</summary>
            <p>{copy}</p>
            {index === 1 && <Link to="/simulate">Try the small-world baseline →</Link>}
            {index === 2 && <Link to="/simulate">Try two-community contact →</Link>}
          </details>
        ))}
      </section>
    </main>
  );
}
