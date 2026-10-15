(() => {
  'use strict';
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const colour = matchMedia('(prefers-color-scheme: light)');
  const themeButton = document.querySelector('.theme-button');
  let stored;
  try { stored = localStorage.getItem('nyanime-theme'); } catch { /* Optional storage. */ }
  const theme = value => {
    root.dataset.theme = value;
    const label = value === 'light' ? 'Switch to dark theme' : 'Switch to light theme';
    themeButton?.setAttribute('aria-label', label);
    themeButton?.setAttribute('title', label);
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', value === 'light' ? '#faf2ef' : '#130f16');
  };
  theme(stored === 'light' || stored === 'dark' ? stored : colour.matches ? 'light' : 'dark');
  themeButton?.addEventListener('click', () => {
    stored = root.dataset.theme === 'light' ? 'dark' : 'light';
    theme(stored);
    try { localStorage.setItem('nyanime-theme', stored); } catch { /* Optional storage. */ }
  });
  colour.addEventListener('change', () => { if (!stored) theme(colour.matches ? 'light' : 'dark'); });

  const animations = new Set();
  const reveal = (element, index = 0) => {
    if (reduced.matches || document.hidden || !element.animate) return;
    const animation = element.animate([{opacity: 0, translate: '0 12px'}, {opacity: 1, translate: '0 0'}],
      {duration: 500, delay: Math.min(index * 40, 160), easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards'});
    animations.add(animation);
    const clear = () => animations.delete(animation);
    animation.addEventListener('finish', clear, {once: true});
    animation.addEventListener('cancel', clear, {once: true});
  };
  let observer;
  if ('IntersectionObserver' in window && !reduced.matches) {
    observer = new IntersectionObserver(entries => {
      let index = 0;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer.unobserve(entry.target);
        if (entry.boundingClientRect.top >= 0 && !entry.target.contains(document.activeElement)) reveal(entry.target, index++);
      }
    }, {rootMargin: '0px 0px -12px 0px'});
    document.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element));
  }
  const settle = () => { animations.forEach(animation => animation.cancel()); animations.clear(); };
  document.addEventListener('visibilitychange', () => { root.toggleAttribute('data-motion-paused', document.hidden); if (document.hidden) settle(); });
  reduced.addEventListener('change', () => { if (reduced.matches) { observer?.disconnect(); settle(); } });
  document.addEventListener('focusin', event => { animations.forEach(animation => { if (animation.effect?.target?.contains(event.target)) animation.cancel(); }); });

  const filters = document.querySelector('.demo-filters');
  if (filters) {
    const buttons = [...filters.querySelectorAll('[data-filter]')];
    const cards = [...document.querySelectorAll('.demo-card')];
    const pill = filters.querySelector('.t-tabs-pill');
    const count = document.querySelector('.demo-count');
    const grid = document.querySelector('.demo-grid');
    const context = document.querySelector('.demo-context');
    const pagination = document.querySelector('.demo-pagination');
    const more = pagination?.querySelector('.demo-more');
    const progress = pagination?.querySelector('[data-demo-progress]');
    const families = {
      all: ['Video, manga, news & TV', 'Original pages, ready to explore. Choose a family to see its contract.', 'Compare the APIs', 'choosing-a-family'],
      video: ['From discovery to playback.', 'Title details, episode lists, video qualities and subtitle tracks.', 'Video contract', 'video-adapter'],
      manga: ['From the first chapter to the last page.', 'Title details, chapter lists and pages in reading order.', 'Manga contract', 'manga-adapter'],
      news: ['Articles that feel at home.', 'Search, pagination and native article blocks with text and images.', 'News contract', 'news-adapter'],
      tv: ['A small signal. A real integration.', 'A finite test stream. No live programme guide or invented broadcasts.', 'TV contract', 'tv-adapter']
    };
    let currentFilter = 'all';
    let visibleLimit = 8;
    const renderCards = () => {
      const matching = cards.filter(card => currentFilter === 'all' || currentFilter === card.dataset.kind);
      const shown = matching.slice(0, visibleLimit);
      const shownSet = new Set(shown);
      cards.forEach(card => { card.hidden = !shownSet.has(card); });
      if (grid) grid.dataset.filter = currentFilter;
      if (count) count.textContent = `${matching.length} ${matching.length === 1 ? 'demo' : 'demos'} to explore`;
      if (progress) progress.textContent = `${shown.length} of ${matching.length} ${matching.length === 1 ? 'example' : 'examples'}`;
      if (pagination) pagination.hidden = matching.length <= 8;
      if (more) {
        const remaining = matching.length - shown.length;
        more.hidden = remaining === 0;
        more.firstChild.textContent = remaining ? `Show ${Math.min(8, remaining)} more ${remaining === 1 ? 'example' : 'examples'} ` : '';
      }
      return shown;
    };
    const updateContext = () => {
      if (!context) return;
      const [heading, description, label, anchor] = families[currentFilter];
      context.querySelector('[data-demo-heading]').textContent = heading;
      context.querySelector('[data-demo-description]').textContent = description;
      const link = context.querySelector('[data-demo-guide]');
      link.firstChild.textContent = `${label} `;
      link.href = `/example/guide/#${anchor}`;
      context.hidden = false;
    };
    const movePill = instant => {
      const selected = buttons.find(button => button.getAttribute('aria-pressed') === 'true');
      if (!selected || !pill) return;
      if (instant) pill.style.transition = 'none';
      pill.style.width = `${selected.offsetWidth}px`;
      pill.style.transform = `translateX(${selected.offsetLeft}px)`;
      if (instant) { void pill.offsetWidth; pill.style.transition = ''; }
    };
    filters.dataset.enhanced = '';
    movePill(true);
    renderCards();
    updateContext();
    const choose = selected => {
      if (selected.getAttribute('aria-pressed') === 'true') return;
      buttons.forEach(button => button.setAttribute('aria-pressed', String(button === selected)));
      movePill(false);
      currentFilter = selected.dataset.filter;
      visibleLimit = 8;
      // A local fade avoids taking a full-page snapshot of a long demo grid.
      // Set the content immediately, including during rapid filter changes.
      grid?.getAnimations().forEach(animation => animation.cancel());
      renderCards();
      updateContext();
      if (grid && !reduced.matches && grid.animate) {
        const animation = grid.animate([{opacity: .35}, {opacity: 1}],
          {duration: 250, easing: 'cubic-bezier(.22,1,.36,1)'});
        animations.add(animation);
        const clear = () => animations.delete(animation);
        animation.addEventListener('finish', clear, {once: true});
        animation.addEventListener('cancel', clear, {once: true});
      }
    };
    more?.addEventListener('click', event => {
      const previouslyShown = new Set(cards.filter(card => !card.hidden));
      visibleLimit += 8;
      const added = renderCards().filter(card => !previouslyShown.has(card));
      added.forEach((card, index) => reveal(card, index));
      // Keep keyboard focus in the newly revealed content, including when the
      // final page removes the button. Pointer activation keeps its position.
      if (event.detail === 0) added[0]?.focus();
      else if (more.hidden && document.activeElement === more) more.blur();
    });
    buttons.forEach((button, index) => {
      button.addEventListener('click', () => choose(button));
      button.addEventListener('keydown', event => {
        const delta = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
        if (!delta && event.key !== 'Home' && event.key !== 'End') return;
        event.preventDefault();
        const next = event.key === 'Home' ? buttons[0] : event.key === 'End' ? buttons[buttons.length - 1] : buttons[(index + delta + buttons.length) % buttons.length];
        next.focus(); choose(next);
      });
    });
    if ('ResizeObserver' in window) new ResizeObserver(() => movePill(true)).observe(filters);
    document.fonts?.ready.then(() => movePill(true));
  }

  // The guide remains fully readable without JavaScript. Enhance its existing
  // index without changing section IDs or the source-generated article body.
  const guideLinks = [...document.querySelectorAll('.doc-index a')];
  if (guideLinks.length && 'IntersectionObserver' in window) {
    const guideObserver = new IntersectionObserver(entries => {
      const current = entries.filter(entry => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!current) return;
      guideLinks.forEach(link => {
        if (link.hash === `#${current.target.id}`) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, {rootMargin: '-130px 0px -55% 0px'});
    document.querySelectorAll('.docs-article h2[id]').forEach(heading => guideObserver.observe(heading));
  }
  document.querySelectorAll('.doc-toc a').forEach(link => link.addEventListener('click', () => {
    link.closest('details').open = false;
  }));

  const video = document.querySelector('.cinema-frame video');
  document.querySelectorAll('[data-quality]').forEach(button => button.addEventListener('click', () => {
    if (!video || button.getAttribute('aria-pressed') === 'true') return;
    const source = video.querySelector(`source[data-height="${button.dataset.quality}"]`);
    if (!source) return;
    const position = video.currentTime;
    const playing = !video.paused;
    document.querySelectorAll('[data-quality]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    video.src = source.src;
    video.addEventListener('loadedmetadata', () => { video.currentTime = Math.min(position, video.duration || position); if (playing) video.play().catch(() => {}); }, {once: true});
    video.load();
  }));

  if (navigator.clipboard) document.querySelectorAll('.docs-article pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'copy-code'; button.textContent = 'Copy'; button.setAttribute('aria-label', 'Copy code snippet');
    const feedback = label => {
      button.textContent = label;
      button.setAttribute('aria-label', label);
      setTimeout(() => { button.textContent = 'Copy'; button.setAttribute('aria-label', 'Copy code snippet'); }, 1800);
    };
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code.textContent); feedback('Copied'); }
      catch {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(code);
        selection?.removeAllRanges();
        selection?.addRange(range);
        feedback(selection?.toString() ? 'Text selected' : 'Select code manually');
      }
    });
    pre.append(button);
  });
})();
