import React from 'react';
import '../../styles/landing.css';

interface FeatureCardProps {
  icon: React.ReactNode;
  step: string;
  title: string;
  description: string;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({ icon, step, title, description }) => {
  return (
    <div className="feature-card">
      <div className="feature-card-icon-area">
        {icon}
      </div>
      <div className="feature-card-content">
        <span className="feature-card-step">{step}</span>
        <h3 className="feature-card-title">{title}</h3>
        <p className="feature-card-desc">{description}</p>
      </div>
    </div>
  );
};
