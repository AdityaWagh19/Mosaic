import React from 'react';
import { SimulationProvider } from './contexts/SimulationContext';
import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <SimulationProvider>
      <Dashboard />
    </SimulationProvider>
  );
}

export default App;
