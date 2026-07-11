/**
 * src/__tests__/ExperimentsPage.test.tsx
 *
 * Tests for the ExperimentsPage:
 *   - Filter pills render for all experiment categories
 *   - Clicking a filter pill narrows the displayed sections
 *   - "No figures" notice shown when available array is empty
 *   - All experiments listed when filter is 'all'
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const mockExperiments = [
  {
    id: 'topology',
    title: 'Topology comparison',
    summary: 'Compare how different network structures shape diversity.',
    figures: ['e1_diversity_timeseries.png'],
    available: ['e1_diversity_timeseries.png'],
  },
  {
    id: 'prestige',
    title: 'Prestige and centrality',
    summary: 'Test whether highly connected speakers exert more influence.',
    figures: ['e2_centrality_vs_influence.png'],
    available: [], // no figures generated yet
  },
];

vi.mock('../api/client', () => ({
  fetchExperiments: vi.fn().mockResolvedValue({ items: mockExperiments }),
  figureUrl: (name: string) => `/api/figures/${name}`,
}));

async function renderExperiments() {
  const { ExperimentsPage } = await import('../pages/ExperimentsPage');
  return render(
    <MemoryRouter>
      <ExperimentsPage nav={<nav />} />
    </MemoryRouter>
  );
}

describe('ExperimentsPage', () => {
  it('renders filter pills including All and each category', async () => {
    await renderExperiments();
    expect(screen.getByRole('button', { name: /all experiments/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /topology/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /prestige/i })).toBeInTheDocument();
  });

  it('shows all experiments by default', async () => {
    await renderExperiments();
    await waitFor(() =>
      expect(screen.getByText('Topology comparison')).toBeInTheDocument()
    );
    expect(screen.getByText('Prestige and centrality')).toBeInTheDocument();
  });

  it('clicking a filter pill narrows displayed experiments', async () => {
    await renderExperiments();
    await waitFor(() =>
      expect(screen.getByText('Topology comparison')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('button', { name: /topology comparison/i }));
    // Only topology should remain visible
    expect(screen.getByText('Topology comparison')).toBeInTheDocument();
    expect(screen.queryByText('Prestige and centrality')).not.toBeInTheDocument();
  });

  it('shows "no figures" notice when available is empty', async () => {
    await renderExperiments();
    await waitFor(() =>
      expect(screen.getByText(/no figures available yet/i)).toBeInTheDocument()
    );
  });
});
