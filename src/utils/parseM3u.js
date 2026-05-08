/**
 * Lightweight browser-side M3U/M3U8 playlist parser.
 * No Node.js dependencies — works directly in the browser.
 */
export function parseM3u(text) {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  const channels = [];

  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].startsWith('#EXTINF')) continue;

    const extinf = lines[i];
    const url = lines[i + 1];

    if (!url || url.startsWith('#')) continue;

    // Channel name — everything after the last comma
    const nameMatch = extinf.match(/,(.+)$/);
    const name = nameMatch ? nameMatch[1].trim() : 'Unknown';

    // Attribute helpers
    const attr = (key) => {
      const m = extinf.match(new RegExp(`${key}="([^"]*)"`));
      return m ? m[1] : '';
    };

    channels.push({
      name,
      url,
      tvg: {
        id: attr('tvg-id'),
        name: attr('tvg-name'),
        logo: attr('tvg-logo'),
      },
      group: { title: attr('group-title') },
      lang: attr('tvg-language'),
    });

    i++; // skip URL line
  }

  return channels;
}
