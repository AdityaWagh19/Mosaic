import { Github, Linkedin, Twitter, Mail } from 'lucide-react';

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-content">
        {/* Left Column: Profile */}
        <div className="footer-profile">
          <img 
            src="/IMG_20260604_162406_502.webp" 
            alt="Aditya Wagh" 
            className="footer-avatar" 
            loading="lazy"
          />
          <div className="footer-profile-text">
            <strong>Aditya Wagh</strong>
            <p>Obsessed with understanding how things work.</p>
          </div>
        </div>

        {/* Center Column: Social Links */}
        <div className="footer-socials">
          <a href="https://github.com/AdityaWagh19" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
            <Github size={20} />
          </a>
          <a href="https://www.linkedin.com/in/adityawaghcse/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
            <Linkedin size={20} />
          </a>
          <a href="https://x.com/AdityaaWagh" target="_blank" rel="noopener noreferrer" aria-label="X (Twitter)">
            <Twitter size={20} />
          </a>
          <a href="mailto:awagh5368@gmail.com" aria-label="Email">
            <Mail size={20} />
          </a>
        </div>

        {/* Right Column: Copyright */}
        <div className="footer-copyright">
          <p>&copy; 2026 Aditya Wagh</p>
        </div>
      </div>
    </footer>
  );
}
