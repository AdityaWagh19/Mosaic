import React from 'react';
import '../../styles/landing.css';

interface UseCaseCardProps {
  label: string;
  gradientClass: string; // Used to apply a specific gradient background
}

export const UseCaseCard: React.FC<UseCaseCardProps> = ({ label, gradientClass }) => {
  return (
    <div className="usecase-card">
      <div className={`usecase-gradient ${gradientClass}`}></div>
      <div className="usecase-label-container">
        <span className="usecase-label">{label}</span>
      </div>
    </div>
  );
};
