import { useState } from 'react';
import { Search, Star, Tv2, StarOff } from 'lucide-react';

function ChannelLogo({ channel }) {
  const [imgError, setImgError] = useState(false);
  const initials = channel.name ? channel.name.slice(0, 2).toUpperCase() : 'TV';

  if (channel.tvg?.logo && !imgError) {
    return (
      <img
        className="channel-logo"
        src={channel.tvg.logo}
        alt={channel.name}
        onError={() => setImgError(true)}
      />
    );
  }

  return (
    <div className="channel-logo-fallback">{initials}</div>
  );
}

export default function Sidebar({ channels, favorites, activeChannel, onSelect, onToggleFav }) {
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState('all');

  const filtered = channels.filter((ch) => {
    const matchesSearch = (ch.name || '').toLowerCase().includes(search.toLowerCase());
    const matchesFav = tab === 'favorites' ? favorites.has(ch.url) : true;
    return matchesSearch && matchesFav;
  });

  return (
    <aside className="sidebar">
      <div className="sidebar-search">
        <div className="search-wrapper">
          <Search size={15} className="search-icon" />
          <input
            id="channel-search"
            type="text"
            className="search-input"
            placeholder="Search channels..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="sidebar-tabs">
        <button
          id="tab-all"
          className={`tab-btn ${tab === 'all' ? 'active' : ''}`}
          onClick={() => setTab('all')}
        >
          <Tv2 size={14} />
          All
          <span className="sidebar-count">{channels.length}</span>
        </button>
        <button
          id="tab-favorites"
          className={`tab-btn ${tab === 'favorites' ? 'active' : ''}`}
          onClick={() => setTab('favorites')}
        >
          <Star size={14} />
          Favorites
          <span className="sidebar-count">{favorites.size}</span>
        </button>
      </div>

      <div className="channel-list">
        {filtered.length === 0 ? (
          <div className="empty-state">
            <StarOff size={32} />
            <p>
              {tab === 'favorites'
                ? 'No favorites yet. Star a channel!'
                : 'No channels match your search.'}
            </p>
          </div>
        ) : (
          filtered.map((ch, idx) => (
            <div
              key={ch.url + idx}
              id={`channel-${idx}`}
              className={`channel-item ${activeChannel?.url === ch.url ? 'active' : ''}`}
              onClick={() => onSelect(ch)}
            >
              <ChannelLogo channel={ch} />
              <div className="channel-info">
                <div className="channel-name">{ch.name || 'Unknown Channel'}</div>
                {ch.group?.title ? (
                  <div className="channel-group">{String(ch.group.title)}</div>
                ) : null}
              </div>
              <button
                className={`fav-btn ${favorites.has(ch.url) ? 'active' : ''}`}
                title={favorites.has(ch.url) ? 'Remove from favorites' : 'Add to favorites'}
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleFav(ch.url);
                }}
              >
                <Star size={14} fill={favorites.has(ch.url) ? 'currentColor' : 'none'} />
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
