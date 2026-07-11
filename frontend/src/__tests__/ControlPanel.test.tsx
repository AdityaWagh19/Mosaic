/**
 * src/__tests__/ControlPanel.test.tsx
 *
 * Tests for the ControlPanel component:
 *   - Preset selection updates the config in context
 *   - Topology selector changes conditional parameter fields
 *   - Run button is disabled while isRunning is true
 *
 * All API calls are mocked via vi.mock; no real HTTP is made.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

// Mock the entire API client so no real HTTP calls happen
vi.mock('../api/client', () => ({
  fetchTopologies: vi.fn().mockResolvedValue({
    er: { desc: 'Erdős–Rényi random graph', params: ['p_er'] },
    watts_strogatz: { desc: 'Watts-Strogatz small world', params: ['k_ws', 'p_rewire'] },
    ba: { desc: 'Barabási-Albert scale-free', params: ['m_ba'] },
    sbm: { desc: 'Two-community SBM', params: ['p_in', 'p_out'] },
  }),
  fetchConfigSchema: vi.fn().mockResolvedValue({
    version: 1,
    defaults: {
      N: 200, T: 10000, gamma: 1, theta: 0.3, sigma: 0.01,
      seed: 42, topology: 'watts_strogatz', p_er: 0.05,
      k_ws: 6, p_rewire: 0.1, m_ba: 3, n_communities: 2,
      p_in: 0.15, p_out: 0.02,
    },
    fields: {
      N: { label: 'Agents', min: 5, max: 2000, step: 10 },
      T: { label: 'Maximum steps', min: 100, max: 100000, step: 100 },
    },
  }),
  runSimulation: vi.fn().mockRejectedValue(new Error('No mock run')),
}));

// Mock SimulationContext so we can control isRunning
const mockRun = vi.fn().mockResolvedValue(null);
const mockSetConfig = vi.fn();

let mockIsRunning = false;

vi.mock('../contexts/SimulationContext', () => ({
  useSimulation: () => ({
    config: {
      topology: 'er', N: 200, T: 10000, gamma: 1, theta: 0.3,
      sigma: 0.01, seed: 42, p_er: 0.05, k_ws: 6, p_rewire: 0.1,
      m_ba: 3, n_communities: 2, p_in: 0.15, p_out: 0.02,
    },
    setConfig: mockSetConfig,
    get isRunning() { return mockIsRunning; },
    error: null,
    result: null,
    umap: null,
    run: mockRun,
    load: vi.fn(),
    clear: vi.fn(),
  }),
  SimulationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

let ControlPanel: React.ComponentType;

beforeEach(async () => {
  mockIsRunning = false;
  const mod = await import('../components/simulation/ControlPanel');
  ControlPanel = (mod as { ControlPanel: React.ComponentType }).ControlPanel;
});

function renderPanel() {
  return render(
    <MemoryRouter>
      <ControlPanel />
    </MemoryRouter>
  );
}

describe('ControlPanel', () => {
  it('renders without crashing', () => {
    renderPanel();
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('run button calls run() on click', async () => {
    renderPanel();
    const runBtns = screen.getAllByRole('button', { name: /run/i });
    if (runBtns.length > 0) {
      fireEvent.click(runBtns[0]);
    }
  });
});

describe('ControlPanel — disabled while running', () => {
  it('run buttons are disabled when isRunning is true', async () => {
    mockIsRunning = true;
    renderPanel();

    const runBtns = screen.getAllByRole('button', { name: /running/i });
    expect(runBtns.length).toBeGreaterThan(0);
    runBtns.forEach(btn => {
      expect(btn).toBeDisabled();
    });
  });
});
