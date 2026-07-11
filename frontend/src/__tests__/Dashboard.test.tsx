/**
 * src/__tests__/Dashboard.test.tsx
 *
 * Tests for the Dashboard page:
 *   - Loading spinner renders while isRunning
 *   - Error notice renders on error
 *   - Empty prompt renders with no result
 *   - Completed result renders metrics and tab list
 *   - Tab click updates ?tab= search param
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

vi.mock('../api/client', () => ({
  exportUrl: (_id: string, fmt: string) => `/api/runs/test/export?format=${fmt}`,
  fetchUmap: vi.fn().mockResolvedValue({ snapshots: [] }),
  fetchResult: vi.fn().mockResolvedValue(null),
}));

const makeContext = (overrides = {}) => ({
  config: {
    topology: 'er', N: 200, T: 10000, gamma: 1, theta: 0.3,
    sigma: 0.01, seed: 42, p_er: 0.05, k_ws: 6, p_rewire: 0.1,
    m_ba: 3, n_communities: 2, p_in: 0.15, p_out: 0.02,
  },
  setConfig: vi.fn(),
  result: null,
  umap: null,
  isRunning: false,
  error: null,
  run: vi.fn(),
  load: vi.fn(),
  clear: vi.fn(),
  ...overrides,
});

const mockResult = {
  run_id: 'er_42',
  config: { topology: 'er', N: 10, T: 100, gamma: 1, theta: 0.3, sigma: 0.01, seed: 42, p_er: 0.5, k_ws: 6, p_rewire: 0.1, m_ba: 3, n_communities: 2, p_in: 0.15, p_out: 0.02 },
  metrics: { convergence_time: 50, converged: true, final_diversity: 0.12, final_pairwise_distance: 0.08 },
  timeline: [{ timestep: 0, diversity: 0.9, pairwise_distance: 0.4 }],
  final_agent_states: [],
  network: { nodes: [], edges: [] },
};

let contextValue = makeContext();

vi.mock('../contexts/SimulationContext', () => ({
  useSimulation: () => contextValue,
  SimulationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Stub heavy visualisation components
vi.mock('../components/visualizations/NetworkGraph', () => ({ NetworkGraph: () => <div data-testid="network-graph" /> }));
vi.mock('../components/visualizations/UmapScatter', () => ({ UmapScatter: () => <div data-testid="umap-scatter" /> }));
vi.mock('../components/visualizations/TimeSeriesChart', () => ({ TimeSeriesChart: () => <div data-testid="timeseries-chart" /> }));
vi.mock('../components/visualizations/SnapshotPlayback', () => ({ SnapshotPlayback: () => <div data-testid="snapshot-playback" /> }));
vi.mock('../components/simulation/ControlPanel', () => ({ ControlPanel: () => <div data-testid="control-panel" /> }));

async function renderDashboard(path = '/simulate') {
  const { Dashboard } = await import('../pages/Dashboard');
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/simulate" element={<Dashboard nav={<nav />} />} />
        <Route path="/runs/:runId" element={<Dashboard nav={<nav />} />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('Dashboard — empty state', () => {
  it('shows empty prompt when no result', async () => {
    contextValue = makeContext();
    await renderDashboard();
    expect(screen.getByText(/start with a question/i)).toBeInTheDocument();
  });
});

describe('Dashboard — loading state', () => {
  it('shows spinner when isRunning', async () => {
    contextValue = makeContext({ isRunning: true });
    await renderDashboard();
    expect(document.querySelector('.spinner')).toBeInTheDocument();
  });
});

describe('Dashboard — error state', () => {
  it('shows error notice when error is set', async () => {
    contextValue = makeContext({ error: 'Simulation failed due to memory.' });
    await renderDashboard();
    expect(screen.getByText(/this run could not be completed/i)).toBeInTheDocument();
  });
});

describe('Dashboard — completed result', () => {
  it('renders metrics and tab list', async () => {
    contextValue = makeContext({ result: mockResult });
    await renderDashboard();
    expect(screen.getByText(/run complete/i)).toBeInTheDocument();
    expect(screen.getAllByText(/converged/i).length).toBeGreaterThan(0);
    // Four tabs
    expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /network/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /accent space/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /data/i })).toBeInTheDocument();
  });

  it('clicking a tab changes the active tab', async () => {
    contextValue = makeContext({ result: mockResult });
    await renderDashboard();
    const networkTab = screen.getByRole('tab', { name: /network/i });
    fireEvent.click(networkTab);
    await waitFor(() => expect(screen.getByRole('tab', { name: /network/i })).toHaveAttribute('aria-selected', 'true'));
  });
});
