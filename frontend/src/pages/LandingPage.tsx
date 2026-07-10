import React from 'react';
import { useNavigate } from 'react-router-dom';
import { NavBar } from '../components/core/NavBar';
import { Button } from '../components/core/Button';
import { FeatureCard } from '../components/core/FeatureCard';
import { UseCaseCard } from '../components/core/UseCaseCard';
import '../../styles/landing.css';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{ backgroundColor: 'var(--surface-canvas)' }}>
      <NavBar />
      
      <main className="landing-page">
        {/* ── Hero Section ──────────────────────────────────────────────── */}
        <section className="hero-section">
          <h1 className="hero-headline">
            A confident editorial monochrome where the only color is the artwork and the only ornament is the serif.
          </h1>
          <p className="hero-subhead">
            Mosaic provides an agent-based modeling framework designed to map complex, nonlinear interactions with absolute clarity.
          </p>
          <div className="hero-ctas">
            <Button variant="primary" onClick={() => navigate('/simulation')}>
              Run Simulation
            </Button>
            <Button variant="secondary">
              Read Documentation
            </Button>
          </div>
        </section>

        {/* ── Logo Strip ────────────────────────────────────────────────── */}
        <section className="logo-strip">
          <span className="logo-item">MIT</span>
          <span className="logo-item">Stanford</span>
          <span className="logo-item">DeepMind</span>
          <span className="logo-item">OpenAI</span>
          <span className="logo-item">Anthropic</span>
        </section>

        {/* ── Features Grid ─────────────────────────────────────────────── */}
        <section className="features-section">
          <h2 className="section-title">Core Capabilities</h2>
          <div className="features-grid">
            <FeatureCard 
              step="001 TOPOLOGY"
              title="Graph-Native Architecture"
              description="Seamlessly render complex network topologies with D3.js physics, scaling from simple Erdös-Rényi to highly modular Barabási-Albert networks."
              icon={
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="5" r="3" fill="currentColor"/>
                  <circle cx="19" cy="19" r="3" fill="currentColor"/>
                  <circle cx="5" cy="19" r="3" fill="currentColor"/>
                  <path d="M11 7L7 17M13 7L17 17M7 19H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              }
            />
            <FeatureCard 
              step="002 EMBEDDING"
              title="UMAP Dimensionality"
              description="Project high-dimensional agent states down to 2D in real-time, providing an interactive, scrubbable timeline of cultural polarization and convergence."
              icon={
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 20H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <path d="M4 4V20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <circle cx="10" cy="14" r="2" fill="currentColor"/>
                  <circle cx="16" cy="8" r="2" fill="currentColor"/>
                </svg>
              }
            />
          </div>
        </section>

        {/* ── Use Cases Grid ────────────────────────────────────────────── */}
        <section className="usecases-section">
          <h2 className="section-title">Experiment Modules</h2>
          <div className="usecases-grid">
            <UseCaseCard label="Cultural Assimilation" gradientClass="grad-1" />
            <UseCaseCard label="Opinion Polarization" gradientClass="grad-2" />
            <UseCaseCard label="Epidemic Spreading" gradientClass="grad-3" />
          </div>
        </section>
      </main>
    </div>
  );
};
