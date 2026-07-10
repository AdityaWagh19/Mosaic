import React from 'react';
import { NavBar } from '../components/core/NavBar';
import '../styles/layout.css';

interface MainLayoutProps {
  sidebar: React.ReactNode;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ sidebar, children }) => {
  return (
    <div className="layout">
      <div style={{ gridColumn: '1 / -1' }}>
        <NavBar />
      </div>
      {sidebar}
      <main className="canvas">
        {children}
      </main>
    </div>
  );
};
