import { lazy, Suspense } from 'react';

import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import * as Popover from '@radix-ui/react-popover';
import { Menu, Play, ChevronDown } from 'lucide-react';
import { SimulationProvider, useSimulation } from './contexts/SimulationContext';
import { GuidePage } from './pages/GuidePage';
import { ApiStatus } from './components/ui/ApiStatus';
import { SiteFooter } from './components/ui/SiteFooter';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { ScrollProgress } from './components/ui/motion/ScrollProgress';
import { MagneticButton } from './components/ui/motion/MagneticButton';

const LandingPage = lazy(() => import('./pages/LandingPage').then(module => ({ default: module.LandingPage })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const ExperimentsPage = lazy(() => import('./pages/ExperimentsPage').then(module => ({ default: module.ExperimentsPage })));
const ComparePage = lazy(() => import('./pages/ComparePage').then(module => ({ default: module.ComparePage })));
const AnalysisPage = lazy(() => import('./pages/AnalysisPage').then(module => ({ default: module.AnalysisPage })));

function Nav() {
  const { run } = useSimulation();
  const location = useLocation();

  return (
    <nav className="nav" aria-label="Main navigation">
      <Link className="brand" to="/" aria-label="Mosaic home">
        <img src="/brand/mosaic-logo.png" alt="" width={22} height={22} style={{ display: 'block' }} />
        <span>Mosaic</span>
      </Link>
      <div className="nav-links">
        <NavLink to="/">Home</NavLink>
        <NavLink to="/simulate">Simulator</NavLink>
        
        <Popover.Root>
          <Popover.Trigger className="research-menu-trigger">
            Research <ChevronDown size={14} className="nav-chevron" />
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
              <NavLink to="/">Home</NavLink>
              <NavLink to="/simulate">Simulator</NavLink>
              <NavLink to="/experiments">Experiments</NavLink>
              <NavLink to="/compare">Compare runs</NavLink>
              <NavLink to="/analysis">ML analysis</NavLink>
              <NavLink to="/guide">Method</NavLink>
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      </div>

      <MagneticButton>
        <Link className="btn btn-primary nav-cta" to="/simulate" onClick={(e) => {
          if (location.pathname === '/simulate') {
            e.preventDefault();
            void run();
          }
        }}>
          <Play size={16} aria-hidden="true" className="btn-icon" /> Run a simulation
        </Link>
      </MagneticButton>
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
      <SiteFooter />
    </main>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <SimulationProvider>
          <AppRoutes />
        </SimulationProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

function AppRoutes() { 
  const location = useLocation(); 
  
  return (
    <Suspense fallback={<main className="shell"><Nav /><div className="empty"><span className="spinner" aria-label="Loading" /></div><SiteFooter /></main>}>
      <ScrollProgress />
      <ApiStatus />
      <Routes location={location}>
            <Route path="/" element={<><LandingPage nav={<Nav />} /><SiteFooter /></>} />
            <Route path="/simulate" element={<><Dashboard nav={<Nav />} /><SiteFooter /></>} />
            <Route path="/runs/:runId" element={<><Dashboard nav={<Nav />} /><SiteFooter /></>} />
            <Route path="/experiments" element={<><ExperimentsPage nav={<Nav />} /><SiteFooter /></>} />
            <Route path="/compare" element={<><ComparePage nav={<Nav />} /><SiteFooter /></>} />
            <Route path="/analysis" element={<><AnalysisPage nav={<Nav />} /><SiteFooter /></>} />
            <Route path="/guide" element={<><GuidePage nav={<Nav />} /><SiteFooter /></>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
    </Suspense>
  ); 
}
