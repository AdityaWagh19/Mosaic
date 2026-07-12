import { Link } from 'react-router-dom';
import { SpotlightCard } from '../components/ui/motion/SpotlightCard';
import { StaggerFade } from '../components/ui/motion/StaggerFade';
import { BlurReveal } from '../components/ui/motion/BlurReveal';
import { LineReveal } from '../components/ui/motion/LineReveal';
import { IllustrationNetwork } from '../components/ui/IllustrationNetwork';
import { Network, TrendingDown, Hash, GitBranch, Star, Users } from 'lucide-react';

export function LandingPage({ nav }: { nav: React.ReactNode }) {
  return (
    <main className="shell">
      {nav}
      <section className="hero landing-hero" style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 64, alignItems: 'center' }}>
        <div>
          <p className="eyebrow">AGENT-BASED SOCIOLINGUISTICS</p>
          <BlurReveal as="h1">See how social structure shapes accent change.</BlurReveal>
          <p className="lede">Mosaic lets you test how local influence, network structure, and random drift can make accents converge, cluster, or persist.</p>
          <div className="actions">
            <Link className="btn btn-primary" to="/simulate">Run a simulation →</Link>
            <Link className="btn btn-secondary" to="/guide">Learn how it works</Link>
          </div>
        </div>
        <div className="hero-illustration">
          <IllustrationNetwork />
        </div>
      </section>

      <LineReveal className="section-divider" />

      <section className="run-glance" aria-label="What a completed simulation produces">
        <div>
          <p className="eyebrow">A RUN AT A GLANCE</p>
          <BlurReveal as="h2">From a social question to inspectable evidence.</BlurReveal>
          <p>A completed run gives you a convergence outcome, a changing diversity trajectory, a social network, and a projection of accent similarity.</p>
        </div>
        <div className="glance-metrics">
          <div><TrendingDown size={18} className="glance-icon" /><span>Outcome</span><strong>Converged or persistent</strong></div>
          <div><Network size={18} className="glance-icon" /><span>Evidence</span><strong>Network + accent space</strong></div>
          <div><Hash size={18} className="glance-icon" /><span>Reproducible</span><strong>Configuration and seed</strong></div>
        </div>
      </section>

      <section className="section">
        <BlurReveal as="h2">Questions you can explore</BlurReveal>
        <div className="grid">
          <StaggerFade>
            <SpotlightCard className="feature-card">
              <GitBranch size={20} className="feature-icon" />
              <h3>Does topology matter?</h3>
              <p>Compare random, small-world, scale-free, and two-community networks.</p>
            </SpotlightCard>
            <SpotlightCard className="feature-card">
              <Star size={20} className="feature-icon" />
              <h3>Do hubs shape the outcome?</h3>
              <p>Increase prestige influence to test whether central speakers pull others toward them.</p>
            </SpotlightCard>
            <SpotlightCard className="feature-card">
              <Users size={20} className="feature-icon" />
              <h3>When do communities merge?</h3>
              <p>Change bridge density to see when separated groups begin to share an accent pattern.</p>
            </SpotlightCard>
          </StaggerFade>
        </div>
      </section>

      <LineReveal className="section-divider" />

      <section className="section credibility">
        <p className="eyebrow">RESEARCH SURFACES</p>
        <BlurReveal as="h2">Designed as a transparent research demonstration.</BlurReveal>
        <p className="lede">Browse pre-computed experiments, compare reproducible runs, or review the graph-learning benchmark and its limitations.</p>
        
        <div className="citation-pills">
          <span className="citation-pill">Axelrod 1997</span>
          <span className="citation-pill">Deffuant 2000</span>
          <span className="citation-pill">Watts & Strogatz 1998</span>
        </div>

        <div className="actions">
          <Link className="btn btn-secondary" to="/experiments">View experiments</Link>
          <Link className="btn btn-secondary" to="/analysis">Read ML analysis</Link>
        </div>
      </section>
    </main>
  );
}
