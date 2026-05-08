import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import VideoPlayer from './components/VideoPlayer.jsx';
import { useToast } from './hooks/useToast.js';
import { parseM3u } from './utils/parseM3u.js';
import { CheckCircle, XCircle, Info } from 'lucide-react';

// M3U source — uses local file in development, GitHub raw URL in production
const M3U_URL = import.meta.env.DEV 
  ? '/mytv/filtered.m3u' 
  : 'https://raw.githubusercontent.com/tolgakurtuluss/mytv/refs/heads/main/filtered.m3u';

// ─── Toast Container ──────────────────────────────────────────────
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>
          {t.type === 'success' && <CheckCircle size={16} color="var(--green)" />}
          {t.type === 'error'   && <XCircle    size={16} color="var(--red)" />}
          {t.type === 'info'    && <Info        size={16} color="var(--accent-bright)" />}
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────
export default function App() {
  const [channels, setChannels]       = useState([]);
  const [stats, setStats]             = useState(null);
  const [activeChannel, setActiveChannel] = useState(null);
  const [refreshing, setRefreshing]   = useState(false);
  const [toasts, setToasts]           = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { addToast }                  = useToast(setToasts);

  const [favorites, setFavorites] = useState(() => {
    try {
      const saved = localStorage.getItem('iptv-favorites');
      return new Set(saved ? JSON.parse(saved) : []);
    } catch { return new Set(); }
  });

  // ── Fetch & parse M3U from GitHub ────────────────────────────
  const fetchChannels = useCallback(async () => {
    try {
      // Cache-bust so browser doesn't serve a stale response
      const res = await fetch(`${M3U_URL}?t=${Date.now()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      const parsed = parseM3u(text);
      setChannels(parsed);
      setStats({ count: parsed.length, lastUpdate: new Date() });
    } catch (err) {
      addToast('Could not load channel list. Check your connection.', 'error');
    }
  }, [addToast]);

  useEffect(() => { fetchChannels(); }, [fetchChannels]);

  // ── Reload channels (re-fetch M3U) ───────────────────────────
  const handleRefresh = useCallback(async () => {
    if (refreshing) return;
    setRefreshing(true);
    addToast('Reloading channels from GitHub…', 'info');
    try {
      await fetchChannels();
      addToast('Channel list reloaded!', 'success');
    } catch {
      addToast('Reload failed.', 'error');
    } finally {
      setRefreshing(false);
    }
  }, [refreshing, addToast, fetchChannels]);

  // ── Favorites ─────────────────────────────────────────────────
  const handleToggleFav = useCallback((url) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      next.has(url) ? next.delete(url) : next.add(url);
      localStorage.setItem('iptv-favorites', JSON.stringify([...next]));
      return next;
    });
  }, []);

  const handleSelectChannel = useCallback((channel) => {
    setActiveChannel(channel);
    // Close sidebar on mobile after selection
    if (window.innerWidth <= 768) {
      setIsSidebarOpen(false);
    }
  }, []);

  return (
    <div className={`app ${isSidebarOpen ? 'sidebar-open' : ''}`}>
      <Header 
        stats={stats} 
        refreshing={refreshing} 
        onRefresh={handleRefresh} 
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        isSidebarOpen={isSidebarOpen}
      />
      <Sidebar
        isOpen={isSidebarOpen}
        channels={channels}
        favorites={favorites}
        activeChannel={activeChannel}
        onSelect={handleSelectChannel}
        onToggleFav={handleToggleFav}
        onClose={() => setIsSidebarOpen(false)}
      />
      <div 
        className={`mobile-overlay ${isSidebarOpen ? 'show' : ''}`} 
        onClick={() => setIsSidebarOpen(false)} 
      />
      <main className="main">
        <VideoPlayer channel={activeChannel} />
      </main>
      <ToastContainer toasts={toasts} />
    </div>
  );
}
