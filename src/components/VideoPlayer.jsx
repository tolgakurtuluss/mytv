import { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import { Tv, WifiOff } from 'lucide-react';

export default function VideoPlayer({ channel }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [status, setStatus] = useState('idle'); // idle | loading | playing | error

  useEffect(() => {
    if (!channel) { setStatus('idle'); return; }

    const video = videoRef.current;
    if (!video) return;

    setStatus('loading');

    if (hlsRef.current) { hlsRef.current.destroy(); hlsRef.current = null; }

    const url = channel.url;

    if (Hls.isSupported()) {
      const hls = new Hls({ maxBufferLength: 10, maxMaxBufferLength: 30, enableWorker: true });
      hlsRef.current = hls;
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().then(() => setStatus('playing')).catch(() => setStatus('error'));
      });
      hls.on(Hls.Events.ERROR, (_, data) => { if (data.fatal) setStatus('error'); });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      video.addEventListener('loadedmetadata', () => {
        video.play().then(() => setStatus('playing')).catch(() => setStatus('error'));
      });
    } else {
      video.src = url;
      video.play().then(() => setStatus('playing')).catch(() => setStatus('error'));
    }

    return () => {
      if (hlsRef.current) { hlsRef.current.destroy(); hlsRef.current = null; }
      video.src = '';
    };
  }, [channel]);

  if (!channel) {
    return (
      <div className="no-channel">
        <div className="no-channel-icon"><Tv size={36} color="var(--text-muted)" /></div>
        <h2>No Channel Selected</h2>
        <p>Choose a channel from the sidebar to start watching</p>
      </div>
    );
  }

  return (
    <div className="player-wrapper">
      <div className="video-container">
        <video ref={videoRef} controls playsInline />

        {status === 'playing' && (
          <div className="video-overlay">
            <span className="live-badge">LIVE</span>
            <span className="channel-overlay-name">{channel.name}</span>
          </div>
        )}

        {status === 'loading' && (
          <div className="player-spinner" style={{ position: 'absolute' }}>
            <div className="spinner-ring" />
            <span>Loading stream...</span>
          </div>
        )}

        {status === 'error' && (
          <div className="player-error" style={{ position: 'absolute' }}>
            <WifiOff size={48} color="var(--red)" />
            <span>Stream unavailable</span>
            <small style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              {channel.name} may be offline
            </small>
          </div>
        )}
      </div>

      <div className="channel-info-bar">
        <div><h3>{channel.name}</h3></div>
        <div className="channel-meta">
          {channel.group?.title ? <span className="meta-tag">{String(channel.group.title)}</span> : null}
          {channel.lang ? <span className="meta-tag">{channel.lang}</span> : null}
        </div>
      </div>
    </div>
  );
}
