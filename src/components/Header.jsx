import { RefreshCw, Tv, ExternalLink } from 'lucide-react';

const ACTIONS_URL = 'https://github.com/tolgakurtuluss/mytv/actions';

export default function Header({ stats, refreshing, onRefresh }) {
  const lastUpdate = stats?.lastUpdate
    ? new Date(stats.lastUpdate).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
    : null;

  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">
          <Tv size={18} color="#fff" />
        </div>
        <span className="header-title">MyTelevision</span>
      </div>

      <div className="header-stats">
        {lastUpdate && (
          <span className="last-update">Updated {lastUpdate}</span>
        )}

        <div className="stat-badge">
          <span className={`dot ${refreshing ? 'updating' : ''}`} />
          <span>{stats?.count ?? 0} channels</span>
        </div>

        <button
          id="btn-refresh"
          className={`btn-refresh ${refreshing ? 'loading' : ''}`}
          onClick={onRefresh}
          disabled={refreshing}
          title="Reload channels from GitHub"
        >
          <RefreshCw size={14} className={refreshing ? 'spin' : ''} />
          {refreshing ? 'Loading...' : 'Reload'}
        </button>

        <a
          href={ACTIONS_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-actions"
          title="Run filter.py on GitHub Actions"
        >
          <ExternalLink size={14} />
          Update List
        </a>
      </div>
    </header>
  );
}
