'use strict';

(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('.theme-toggle');
  const preference = window.matchMedia('(prefers-color-scheme: dark)');
  let manual = false;
  try { manual = ['light', 'dark'].includes(localStorage.getItem('budihal-theme')); } catch (_) {}
  function updateToggle() {
    if (!toggle) return;
    const dark = root.dataset.theme === 'dark';
    toggle.firstElementChild.textContent = dark ? '☀' : '☾';
    toggle.setAttribute('aria-label', `Switch to ${dark ? 'light' : 'dark'} theme`);
    toggle.setAttribute('title', toggle.getAttribute('aria-label'));
  }
  if (toggle) {
    toggle.hidden = false;
    toggle.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      manual = true;
      try { localStorage.setItem('budihal-theme', root.dataset.theme); } catch (_) {}
      updateToggle();
    });
    preference.addEventListener('change', event => {
      if (!manual) { root.dataset.theme = event.matches ? 'dark' : 'light'; updateToggle(); }
    });
    updateToggle();
  }

  document.querySelectorAll('.filterable').forEach(container => {
    const filter = container.querySelector('.tag-filter');
    if (!filter) return;
    const inputs = [...filter.querySelectorAll('input')];
    const entries = [...container.querySelectorAll('[data-tags]')];
    function apply() {
      const selected = inputs.filter(input => input.checked).map(input => input.value);
      let visible = 0;
      entries.forEach(entry => {
        const tags = JSON.parse(entry.dataset.tags || '[]');
        entry.hidden = selected.length > 0 && !selected.some(tag => tags.includes(tag));
        if (!entry.hidden) visible++;
      });
      container.querySelectorAll('.journal-group').forEach(group => {
        group.hidden = ![...group.querySelectorAll('[data-tags]')].some(entry => !entry.hidden);
      });
      filter.querySelector('.filter-count').textContent = selected.length ? `(${selected.length})` : '';
      container.querySelector('.filter-status').textContent = `${visible} ${visible === 1 ? 'entry' : 'entries'} shown`;
      container.querySelector('.filter-empty').hidden = visible !== 0;
    }
    filter.hidden = false;
    filter.addEventListener('change', apply);
    filter.querySelector('.clear-filter').addEventListener('click', () => {
      inputs.forEach(input => { input.checked = false; });
      apply();
    });
    apply();
  });

  document.querySelectorAll('.prose table').forEach(table => {
    const scroll = document.createElement('div');
    scroll.className = 'table-scroll';
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', 'Scrollable table');
    table.before(scroll);
    scroll.append(table);
  });
  const toc = document.querySelector('[data-toc] ul');
  if (toc) {
    document.querySelectorAll('.article-body h2, .article-body h3').forEach((heading, i) => {
      if (!heading.id) heading.id = `section-${i + 1}`;
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = `#${heading.id}`;
      link.textContent = heading.textContent;
      li.append(link); toc.append(li);
    });
    if (!toc.children.length) toc.parentElement.hidden = true;
  }

  function safeUrl(value) {
    try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; } catch (_) { return null; }
  }
  const listeningWidgets = document.querySelectorAll('[data-lastfm]');
  function refreshListening() {
    const requests = new Map();
    listeningWidgets.forEach(async widget => {
    try {
      const source = widget.dataset.source;
      if (!requests.has(source)) {
        requests.set(source, fetch(source, { cache: 'no-store', signal: AbortSignal.timeout(6000) }).then(response => {
          if (!response.ok) throw new Error('Listening history unavailable');
          return response.json();
        }));
      }
      const data = await requests.get(source);
      if (!Array.isArray(data.tracks) || !data.tracks.length) return;
      const fresh = Date.now() - Date.parse(data.updated_at) < 10 * 60 * 1000;
      const list = document.createElement('ul');
      list.className = 'track-list';
      list.setAttribute('role', 'list');
      const compact = widget.dataset.limit === '1';
      const tracks = data.tracks.slice(0, Number(widget.dataset.limit) || 8);
      const buildTrack = (track, index) => {
        const now = fresh && index === 0 && track.now_playing;
        const line = document.createElement(safeUrl(track.url) ? 'a' : 'span');
        if (line.tagName === 'A') line.href = safeUrl(track.url);
        line.textContent = `${now ? '♫ ' : ''}${track.name} · ${track.artist}`;
        if (now) line.setAttribute('aria-label', `Playing at last update: ${track.name} by ${track.artist}`);
        return line;
      };
      if (compact) {
        widget.replaceChildren(buildTrack(tracks[0], 0));
        widget.title = `Last.fm snapshot · updated ${new Date(data.updated_at).toLocaleString()}`;
      } else {
        tracks.forEach((track, index) => {
          const item = document.createElement('li');
          if (widget.dataset.artwork && safeUrl(track.image)) {
            const image = document.createElement('img');
            image.src = safeUrl(track.image); image.alt = ''; image.width = 48; image.height = 48; image.loading = 'lazy';
            image.addEventListener('error', () => image.remove());
            item.append(image);
          }
          const text = document.createElement('div');
          text.append(buildTrack(track, index));
          if (track.album) {
            const album = document.createElement('span');
            album.className = 'track-artist'; album.textContent = track.album; text.append(album);
          }
          item.append(text); list.append(item);
        });
        const timestamp = document.createElement('p');
        timestamp.className = 'metadata';
        timestamp.textContent = `Last.fm snapshot · updated ${new Date(data.updated_at).toLocaleString()}`;
        widget.replaceChildren(list, timestamp);
      }
    } catch (_) {
      // Keep the previous tracks (or static fallback) on transient failures.
    }
    });
  }
  if (listeningWidgets.length) {
    refreshListening();
    setInterval(() => {
      if (!document.hidden) refreshListening();
    }, 60 * 1000);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) refreshListening();
    });
  }
})();
