import React from 'react';
import '../styles/layout.css';

interface SidebarProps {
  children: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({ children }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">Mosaic</h1>
        <div className="sidebar-subtitle">Agent-Based Model</div>
      </div>
      <div className="sidebar-content">
        {children}
      </div>
    </aside>
  );
};
