/**
 * src/__tests__/AnalysisPage.test.tsx
 *
 * Tests for the AnalysisPage:
 *   - Spinner while loading
 *   - Error notice with backend hint when API fails
 *   - Benchmark table rows render when data loads
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const mockAnalysis = {
  mlp: { accuracy: 0.82, macro_f1: 0.79 },
  gcn: { accuracy: 0.74, macro_f1: 0.71 },
  random_chance: 0.2,
  n_train_runs: 80,
  n_test_runs: 20,
  clustering: { kmeans_silhouette: 0.08, dbscan_n_clusters: 1 },
  figures: [],
};

// Default: resolves successfully
const fetchAnalysisMock = vi.fn().mockResolvedValue(mockAnalysis);

vi.mock('../api/client', () => ({
  fetchAnalysis: (...args: unknown[]) => fetchAnalysisMock(...args),
  figureUrl: (name: string) => `/api/figures/${name}`,
}));

async function renderAnalysis() {
  // Re-import after mock to pick up current fetchAnalysisMock binding
  vi.resetModules();
  const { AnalysisPage } = await import('../pages/AnalysisPage');
  return render(
    <MemoryRouter>
      <AnalysisPage nav={<nav />} />
    </MemoryRouter>
  );
}

describe('AnalysisPage — loading state', () => {
  it('renders spinner before data arrives', async () => {
    fetchAnalysisMock.mockReturnValue(new Promise(() => {})); // never resolves
    await renderAnalysis();
    expect(document.querySelector('.spinner, [class*="spinner"]')).toBeInTheDocument();
  });
});

describe('AnalysisPage — error state', () => {
  it('shows error notice with backend hint', async () => {
    fetchAnalysisMock.mockRejectedValue(new Error('ML analysis has not been generated.'));
    await renderAnalysis();
    await waitFor(() =>
      expect(screen.getByText(/could not load analysis results/i)).toBeInTheDocument()
    );
    expect(screen.getByText(/ml_results\.json/i)).toBeInTheDocument();
  });
});

describe('AnalysisPage — data loaded', () => {
  it('renders benchmark table with MLP, GCN, and random rows', async () => {
    fetchAnalysisMock.mockResolvedValue(mockAnalysis);
    await renderAnalysis();
    await waitFor(() => {
      expect(screen.getByText(/model benchmarks/i)).toBeInTheDocument();
      expect(screen.getAllByText(/mlp/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/gcn/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/random chance/i).length).toBeGreaterThan(0);
    });
  });

  it('renders accuracy values from API data', async () => {
    fetchAnalysisMock.mockResolvedValue(mockAnalysis);
    await renderAnalysis();
    await waitFor(() =>
      expect(screen.getAllByText('82.00%').length).toBeGreaterThan(0)
    );
  });
});
