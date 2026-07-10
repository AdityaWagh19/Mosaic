import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from './Button';
import '../../styles/navbar.css';

export const NavBar: React.FC = () => {
  const navigate = useNavigate();

  return (
    <header className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          {/* Logo Mark: Three-dot cluster icon */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="6" cy="12" r="3" fill="var(--color-ink)"/>
            <circle cx="16" cy="6" r="3" fill="var(--color-ink)"/>
            <circle cx="16" cy="18" r="3" fill="var(--color-ink)"/>
            <path d="M7.5 10.5L14.5 7.5" stroke="var(--color-ink)" strokeWidth="1.5" strokeLinecap="round"/>
            <path d="M7.5 13.5L14.5 16.5" stroke="var(--color-ink)" strokeWidth="1.5" strokeLinecap="round"/>
            <path d="M16 9V15" stroke="var(--color-ink)" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <span className="navbar-logo-text">Mosaic</span>
        </Link>
        
        <nav className="navbar-links">
          <Link to="/" className="navbar-link">Product</Link>
          <Link to="/" className="navbar-link">Use Cases</Link>
          <Link to="/" className="navbar-link">Docs</Link>
        </nav>
        
        <div className="navbar-cta">
          <Button variant="primary" onClick={() => navigate('/simulation')}>
            Run Simulation
          </Button>
        </div>
      </div>
    </header>
  );
};
