import React from 'react';

interface CardProps {
  children: React.ReactNode;
  elevated?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, elevated = false, className = '' }) => {
  return (
    <div className={`card ${elevated ? 'card--elevated' : ''} ${className}`}>
      {children}
    </div>
  );
};
