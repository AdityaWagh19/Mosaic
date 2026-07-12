import { lazy, Suspense } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import * as Popover from '@radix-ui/react-popover';
import { Menu, Play } from 'lucide-react';
import { SimulationProvider } from './contexts/SimulationContext';
import { GuidePage } from './pages/GuidePage';
import { ApiStatus } from './components/ui/ApiStatus';

const LandingPage = lazy(() => import('./pages/LandingPage').then(module => ({ default: module.LandingPage })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const ExperimentsPage = lazy(() => import('./pages/ExperimentsPage').then(module => ({ default: module.ExperimentsPage })));
const ComparePage = lazy(() => import('./pages/ComparePage').then(module => ({ default: module.ComparePage })));
const AnalysisPage = lazy(() => import('./pages/AnalysisPage').then(module => ({ default: module.AnalysisPage })));

function Nav() {
  return (
    <nav className="nav" aria-label="Main navigation">
      <Link className="brand" to="/" aria-label="Mosaic home">
        <img src="/brand/mosaic-logo.png" alt="" width={22} height={22} className="brand-mark" />
        <span className="brand-wordmark">Mosaic</span>
      </Link>
      <div className="nav-links">
        <NavLink to="/simulate">Simulator</NavLink>
        
        <Popover.Root>
          <Popover.Trigger className="research-menu-trigger">
            Research
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content className="research-popover" align="center" sideOffset={8}>
              <NavLink to="/experiments">Experiments<span>Guided case studies</span></NavLink>
              <NavLink to="/compare">Compare runs<span>Configuration and outcomes</span></NavLink>
              <NavLink to="/analysis">ML analysis<span>Benchmark evidence</span></NavLink>
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>

        <NavLink to="/guide">Method</NavLink>
      </div>
      
      <div className="mobile-menu">
        <Popover.Root>
          <Popover.Trigger aria-label="Open navigation" className="mobile-menu-trigger">
            <Menu size={20} />
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content className="mobile-popover" align="end" sideOffset={8}>
              <NavLink to="/simulate">Simulator</NavLink>
              <NavLink to="/experiments">Experiments</NavLink>
              <NavLink to="/compare">Compare runs</NavLink>
              <NavLink to="/analysis">ML analysis</NavLink>
              <NavLink to="/guide">Method</NavLink>
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      </div>

      <Link className="btn btn-primary nav-cta" to="/simulate">
        <Play size={16} aria-hidden="true" style={{ marginRight: 6 }} /> Run a simulation
      </Link>
    </nav>
  );
}

function NotFound() {
  return (
    <main className="shell">
      <Nav />
      <div className="empty">
        <div>
          <h2>That page is not here.</h2>
          <p>Return to Mosaic’s simulation studio to start a run.</p>
          <Link className="btn btn-primary" to="/simulate">Open simulator →</Link>
        </div>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <SimulationProvider>
        <AppRoutes />
      </SimulationProvider>
    </BrowserRouter>
  );
}

function AppRoutes() { 
  const location = useLocation(); 
  const reduced = useReducedMotion(); 
  const transition = reduced ? { duration: 0 } : { duration: .16, ease: 'easeOut' as const }; 
  
  return (
    <Suspense fallback={<main className="shell"><Nav /><div className="empty"><span className="spinner" aria-label="Loading" /></div></main>}>
      <ApiStatus />
      <AnimatePresence mode="wait">
        <motion.div key={location.pathname} initial={reduced ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={reduced ? undefined : { opacity: 0 }} transition={transition}>
          <Routes location={location}>
            <Route path="/" element={<LandingPage nav={<Nav />} />} />
            <Route path="/simulate" element={<Dashboard nav={<Nav />} />} />
            <Route path="/runs/:runId" element={<Dashboard nav={<Nav />} />} />
            <Route path="/experiments" element={<ExperimentsPage nav={<Nav />} />} />
            <Route path="/compare" element={<ComparePage nav={<Nav />} />} />
            <Route path="/analysis" element={<AnalysisPage nav={<Nav />} />} />
            <Route path="/guide" element={<GuidePage nav={<Nav />} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </motion.div>
      </AnimatePresence>
    </Suspense>
  ); 
}
