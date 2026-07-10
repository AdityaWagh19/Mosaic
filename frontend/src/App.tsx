import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SimulationProvider } from './contexts/SimulationContext';
import { LandingPage } from './pages/LandingPage';
import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <Router>
      <SimulationProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/simulation" element={<Dashboard />} />
        </Routes>
      </SimulationProvider>
    </Router>
  );
}

export default App;
