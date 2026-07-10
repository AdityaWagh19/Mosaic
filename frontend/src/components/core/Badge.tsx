import React from 'react';

interface BadgeProps {
  label: string | number;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ label, className = '' }) => {
  return (
    <span className={`badge ${className}`}>
      {label}
    </span>
  );
};
