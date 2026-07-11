import { lazy, Suspense } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { SimulationProvider } from './contexts/SimulationContext';

const LandingPage = lazy(() => import('./pages/LandingPage').then(module => ({ default: module.LandingPage })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const ExperimentsPage = lazy(() => import('./pages/ExperimentsPage').then(module => ({ default: module.ExperimentsPage })));
const ComparePage = lazy(() => import('./pages/ComparePage').then(module => ({ default: module.ComparePage })));
const AnalysisPage = lazy(() => import('./pages/AnalysisPage').then(module => ({ default: module.AnalysisPage })));

function Nav() {
  return <nav className="nav" aria-label="Main navigation">
    <Link className="brand" to="/" aria-label="Mosaic home">
      <span className="brand-mark" aria-hidden="true"><img src="/brand/mosaic-wordmark.svg" alt="" /></span>
    </Link>
    <div className="nav-links">
      <NavLink to="/simulate">Simulator</NavLink>
      <details className="research-menu">
        <summary>Research</summary>
        <div className="research-popover">
          <NavLink to="/experiments">Experiments<span>Guided case studies</span></NavLink>
          <NavLink to="/compare">Compare runs<span>Configuration and outcomes</span></NavLink>
          <NavLink to="/analysis">ML analysis<span>Benchmark evidence</span></NavLink>
        </div>
      </details>
      <NavLink to="/guide">Method</NavLink>
    </div>
    <details className="mobile-menu">
      <summary aria-label="Open navigation">Menu</summary>
      <div className="mobile-popover">
        <NavLink to="/simulate">Simulator</NavLink><NavLink to="/experiments">Experiments</NavLink>
        <NavLink to="/compare">Compare runs</NavLink><NavLink to="/analysis">ML analysis</NavLink><NavLink to="/guide">Method</NavLink>
      </div>
    </details>
    <Link className="btn btn-primary nav-cta" to="/simulate">Run a simulation <span aria-hidden="true">→</span></Link>
  </nav>;
}

function Guide() {
  const sections = [
    ['What is a speaker?', 'A speaker is an agent with six synthetic accent features. Mosaic does not represent recorded voices, real people, or demographic groups.'],
    ['How do speakers influence one another?', 'At each step, a connected pair may accommodate when their accents are close enough. Prestige can weight the influence of highly connected speakers.'],
    ['How does the network matter?', 'The network determines who can meet. Random, clustered, hub-dominated, and two-community structures expose different paths for accent change.'],
    ['What do the metrics mean?', 'Diversity describes how accent clusters are distributed. Pairwise distance describes average separation between speaker accent vectors. Convergence means diversity stabilized.'],
    ['What Mosaic does not model', 'Mosaic is a conceptual agent-based model. It does not make claims about real speech communities, identity, geography, or causal mechanisms outside its explicit rules.'],
  ];
  return <main className="shell"><section>{<Nav />}</section><section className="hero compact-hero"><p className="eyebrow">METHOD GUIDE</p><h1>From social ties to accent patterns.</h1><p className="lede">A short guide to the model, its evidence, and its limits.</p></section><section className="method-guide">{sections.map(([title, copy], index) => <details key={title} open={index === 0}><summary>{title}</summary><p>{copy}</p>{index === 1 && <Link to="/simulate">Try the small-world baseline →</Link>}{index === 2 && <Link to="/simulate">Try two-community contact →</Link>}</details>)}</section></main>;
}

function NotFound() {
  return <main className="shell"><Nav /><div className="empty"><div><h2>That page is not here.</h2><p>Return to Mosaic’s simulation studio to start a run.</p><Link className="btn btn-primary" to="/simulate">Open simulator →</Link></div></div></main>;
}

export default function App() {
  return <BrowserRouter><SimulationProvider><AppRoutes /></SimulationProvider></BrowserRouter>;
}
function AppRoutes() { const location = useLocation(); const reduced = useReducedMotion(); const transition = reduced ? { duration: 0 } : { duration: .16, ease: 'easeOut' as const }; return <Suspense fallback={<main className="shell"><Nav /><div className="empty"><span className="spinner" /></div></main>}><AnimatePresence mode="wait"><motion.div key={location.pathname} initial={reduced ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={reduced ? undefined : { opacity: 0 }} transition={transition}><Routes location={location}>
    <Route path="/" element={<LandingPage nav={<Nav />} />} /><Route path="/simulate" element={<Dashboard nav={<Nav />} />} />
    <Route path="/runs/:runId" element={<Dashboard nav={<Nav />} />} /><Route path="/experiments" element={<ExperimentsPage nav={<Nav />} />} />
    <Route path="/compare" element={<ComparePage nav={<Nav />} />} /><Route path="/analysis" element={<AnalysisPage nav={<Nav />} />} />
    <Route path="/guide" element={<Guide />} /><Route path="*" element={<NotFound />} />
  </Routes></motion.div></AnimatePresence></Suspense>; }
