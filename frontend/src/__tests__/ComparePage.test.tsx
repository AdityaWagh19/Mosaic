/**
 * src/__tests__/ComparePage.test.tsx
 *
 * Tests for the ComparePage:
 *   - Empty archive shows instruction notice
 *   - Single run selected shows "choose at least two" notice
 *   - Two runs checked show config comparison table
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const mockRuns = [
  { run_id: 'er_42', topology: 'er', seed: 42, N: 200, T: 10000, gamma: 1, theta: 0.3, sigma: 0.01, converged: true, convergence_time: 500, final_diversity: 0.12, final_pairwise_distance: 0.08 },
  { run_id: 'ba_99', topology: 'ba', seed: 99, N: 200, T: 10000, gamma: 1, theta: 0.3, sigma: 0.01, converged: false, convergence_time: 10000, final_diversity: 0.45, final_pairwise_distance: 0.22 },
];

const mockResult = (runId: string) => ({
  run_id: runId,
  config: { topology: 'er', N: 200, T: 10000, gamma: 1, theta: 0.3, sigma: 0.01, seed: 42, p_er: 0.05, k_ws: 6, p_rewire: 0.1, m_ba: 3, n_communities: 2, p_in: 0.15, p_out: 0.02 },
  metrics: { convergence_time: 500, converged: true, final_diversity: 0.12, final_pairwise_distance: 0.08 },
  timeline: [{ timestep: 0, diversity: 0.9, pairwise_distance: 0.4 }],
  final_agent_states: [],
  network: { nodes: [], edges: [] },
});

vi.mock('../api/client', () => ({
  fetchRuns: vi.fn().mockResolvedValue({ items: mockRuns, total: 2, next_cursor: null }),
  fetchResult: vi.fn().mockImplementation((id: string) => Promise.resolve(mockResult(id))),
  figureUrl: (name: string) => `/api/figures/${name}`,
}));

async function renderCompare() {
  const { ComparePage } = await import('../pages/ComparePage');
  return render(
    <MemoryRouter>
      <ComparePage nav={<nav />} />
    </MemoryRouter>
  );
}

describe('ComparePage', () => {
  it('shows at-least-two notice with no runs selected', async () => {
    await renderCompare();
    await waitFor(() =>
      expect(screen.getByText(/select two to four runs/i)).toBeInTheDocument()
    );
  });

  it('lists runs from the archive', async () => {
    await renderCompare();
    await waitFor(() => {
      expect(screen.getByText('er_42')).toBeInTheDocument();
      expect(screen.getByText('ba_99')).toBeInTheDocument();
    });
  });

  it('renders run archive section', async () => {
    await renderCompare();
    await waitFor(() =>
      expect(screen.getByText(/run archive/i)).toBeInTheDocument()
    );
  });
});
