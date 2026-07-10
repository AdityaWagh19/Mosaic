import React from 'react';
import '../styles/layout.css';

interface MainLayoutProps {
  sidebar: React.ReactNode;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ sidebar, children }) => {
  return (
    <div className="layout">
      {sidebar}
      <main className="canvas">
        {children}
      </main>
    </div>
  );
};
