import { Link } from 'react-router-dom';

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-content">
        <div className="footer-brand">
          <img src="/brand/mosaic-logo.png" alt="" width={18} height={18} style={{ display: 'block' }} />
          <span>Mosaic</span>
        </div>
        <div className="footer-links">
          <Link to="/simulate">Simulator</Link>
          <Link to="/experiments">Experiments</Link>
          <Link to="/compare">Compare</Link>
          <Link to="/analysis">ML Analysis</Link>
          <Link to="/guide">Method</Link>
        </div>
        <div className="footer-copy">
          <p>Created to explore opinion dynamics and collective behavior in social networks.</p>
        </div>
      </div>
    </footer>
  );
}
