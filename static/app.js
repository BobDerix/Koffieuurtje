'use strict';

// ============================================================
// CONFIG
// ============================================================

const SOURCES = [
  {
    id: 'bnetwerk',
    name: 'Bnetwerk',
    color: '#1565c0',
    icon: 'bi-building',
    baseUrl: 'https://www.bibliotheeknetwerk.nl',
    feedUrls: [
      'https://www.bibliotheeknetwerk.nl/rss.xml',
      'https://www.bibliotheeknetwerk.nl/feed',
      'https://www.bibliotheeknetwerk.nl/nieuws/rss.xml',
    ],
  },
  {
    id: 'markdekkers',
    name: 'Mark Dekkers',
    color: '#e65100',
    icon: 'bi-pencil-square',
    baseUrl: 'https://www.markdeckers.net',
    feedUrls: [
      'https://www.markdeckers.net/feeds/posts/default?alt=rss',
      'https://www.markdeckers.net/feeds/posts/default',
    ],
  },
  {
    id: 'bibliotheekblad',
    name: 'Bibliotheekblad',
    color: '#2e7d32',
    icon: 'bi-newspaper',
    baseUrl: 'https://bibliotheekblad.nl',
    feedUrls: [
      'https://bibliotheekblad.nl/feed/',
      'https://bibliotheekblad.nl/feed',
    ],
  },
  {
    id: 'vob',
    name: 'VOB (Vereniging van Openbare Bibliotheken)',
    color: '#6a1b9a',
    icon: 'bi-people-fill',
    baseUrl: 'https://www.vob.nl',
    feedUrls: [
      'https://www.vob.nl/feed/',
      'https://www.vob.nl/rss',
    ],
  },
  {
    id: 'kb',
    name: 'KB - Koninklijke Bibliotheek',
    color: '#00695c',
    icon: 'bi-bank',
    baseUrl: 'https://www.kb.nl',
    feedUrls: [
      'https://www.kb.nl/rss.xml',
      'https://www.kb.nl/nieuws/rss',
      'https://www.kb.nl/feed',
    ],
  },
  {
    id: 'lezen',
    name: 'Lezen.nl / Stichting Lezen',
    color: '#1565c0',
    icon: 'bi-book',
    baseUrl: 'https://www.lezen.nl',
    feedUrls: [
      'https://www.lezen.nl/feed/',
      'https://www.lezen.nl/rss',
    ],
  },
  {
    id: 'probiblio',
    name: 'ProBiblio',
    color: '#558b2f',
    icon: 'bi-diagram-3',
    baseUrl: 'https://www.probiblio.nl',
    feedUrls: [
      'https://www.probiblio.nl/feed/',
      'https://www.probiblio.nl/rss',
    ],
  },
];

const CATEGORIES = {
  'Digitaal':         ['digitaal','e-book','ebook','digitale bibliotheek','app','online','streaming','e-reader','epub','luisterboek','platform','digitalisering','e-content','bibliotheek app','digitale dienst','nbc','cloudlibrary','bolinda','boekenbalie','libris','publiekebibliotheek','kb app'],
  'Beleid':           ['beleid','wet','subsidie','financiering','budget','overheid','ministerie','gemeente','wethouder','bezuiniging','politiek','bibliotheekwet','stelsel','ocw','coalitieakkoord','motie','amendement','bibliotheekbeleid','cultuurnota','prestatieafspraak','wsob','scp-rapport','bibliotheekstelsel'],
  'Lezen & Educatie': ['lezen','onderwijs','jeugd','kinderen','school','laaggeletterdheid','educatie','voorlezen','leesbevordering','taalvaardigheid','taalcoach','leescafé','geletterdheid','alfabetisering','nationale bibliotheekdag','kinderboekenweek','leesmonitor','leesoffensief','taalakkoord','digisterke','nrp','mbo','hbo','basisschool','voortgezet onderwijs','bibliotheek op school','de bibliotheek op school','dbos'],
  'Statistieken':     ['statistieken','cijfers','rapport','onderzoek','data','meting','uitleningen','gebruik','bezoekers','percentage','groei','jaarverslag','monitor','analyse','fno','wsob-monitor','leengedrag','lidmaatschap','leden','leners','uitleencijfers','financieel jaarverslag'],
  'Innovatie':        ['innovatie','technologie','ai','artificial intelligence','automatisering','robot','chatbot','machine learning','smart','makerspace','experiment','pilot','chatgpt','generatieve ai','llm','digital twin','open data','linked data','rfid','zelfbediening','makerslab'],
  'Collectie':        ['collectie','aanwinsten','muziek','film','boeken','tijdschriften','stripboek','magazine','dvd','nbd','selectie','prentenboek','non-fictie','nbd biblion','bruna','thriller','roman','jeugdboek','graphic novel','e-audioboek','boekenbon','bestseller','nieuwe titels'],
  'Organisatie':      ['personeel','bestuur','directie','samenwerking','fusie','verbouwing','opening','sluiting','directeur','medewerker','vrijwilliger','reorganisatie','nieuwbouw','verhuizing','bibliotheekdirecteur','raad van toezicht','nieuwe locatie','filiaal','dependance','balie','ov-chipkaart bibliotheek','bibliotheekauto'],
  'Evenementen':      ['evenement','congres','conferentie','lezing','workshop','festival','tentoonstelling','bijeenkomst','symposium','dag van','manifestatie','themaweek','boekenbal','schrijversweekend','poëzieweek','bibliotheekcongres','bibliotheekmanifest','salon','debat','storytelling','voorstelling'],
  'Personeel & HR':   ['vacature','sollicitatie','cao','arbeidsmarkt','bibliotheekmedewerker','opleidingen','certificering','bijscholing','bisc','bso'],
};

const CAT_ICONS = {
  'Digitaal':         'bi-laptop',
  'Beleid':           'bi-bank2',
  'Lezen & Educatie': 'bi-book-open',
  'Statistieken':     'bi-bar-chart-line',
  'Innovatie':        'bi-lightbulb',
  'Collectie':        'bi-collection',
  'Organisatie':      'bi-people',
  'Evenementen':      'bi-calendar-event',
  'Personeel & HR':   'bi-person-badge',
  'Overig':           'bi-tag',
};

const CACHE_KEY   = 'bibliotheeknieuws_cache';
const CACHE_TTL   = 60 * 60 * 1000; // 1 hour
const AUTO_REFRESH = 60 * 60 * 1000;
const MAX_ARTICLES_PER_SOURCE = 30;

// ============================================================
// STATE
// ============================================================

let allArticles      = [];
let activeCategory   = 'Alle';
let activeSource     = null;
let searchQuery      = '';
let lastFetched      = null;
let refreshTimer     = null;

// ============================================================
// CORS PROXIES  (tried in order)
// ============================================================

const PROXIES = [
  url => `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`,
  url => `https://corsproxy.io/?${encodeURIComponent(url)}`,
  url => `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(url)}`,
];

async function fetchViaProxy(url) {
  for (const makeProxy of PROXIES) {
    try {
      const res = await fetch(makeProxy(url), { signal: AbortSignal.timeout(12000) });
      if (res.ok) {
        const text = await res.text();
        if (text.length > 50) return text;
      }
    } catch (_) {}
  }
  throw new Error(`Kon ${url} niet ophalen`);
}

// ============================================================
// RSS / ATOM PARSING
// ============================================================

function parseXML(xmlText) {
  const parser = new DOMParser();
  const doc    = parser.parseFromString(xmlText, 'text/xml');
  if (doc.querySelector('parsererror')) throw new Error('Ongeldige XML');
  return doc;
}

function getTextContent(node, selectors) {
  for (const sel of selectors) {
    const el = node.querySelector(sel);
    if (el) {
      const text = el.getAttribute('href') || el.getAttribute('url') || el.textContent;
      if (text?.trim()) return text.trim();
    }
  }
  return '';
}

function stripHTML(html) {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent.replace(/\s+/g, ' ').trim();
}

function findImage(node) {
  // media:thumbnail, media:content with url attribute, or enclosure with url attribute
  const media = node.querySelector('thumbnail, content[url], enclosure[url], enclosure[type^="image"]');
  if (media) return media.getAttribute('url') || media.getAttribute('href');
  // <img> in description/content
  const raw = node.querySelector('description, content, summary')?.innerHTML || '';
  const m   = raw.match(/<img[^>]+src=["']([^"']+)["']/i);
  return m ? m[1] : null;
}

function assignCategory(title, summary = '') {
  const text = (title + ' ' + summary).toLowerCase();
  for (const [cat, keywords] of Object.entries(CATEGORIES)) {
    if (keywords.some(kw => text.includes(kw))) return cat;
  }
  return 'Overig';
}

function parseEntries(doc, source) {
  const articles = [];
  // Support RSS <item> and Atom <entry>
  const nodes = [...doc.querySelectorAll('item'), ...doc.querySelectorAll('entry')];

  for (const node of nodes) {
    const title = getTextContent(node, ['title']);
    let url     = getTextContent(node, ['link[rel="alternate"]', 'link:not([rel])', 'link', 'guid', 'id']);
    if (!title || !url || url.startsWith('?')) continue;

    // Make relative URLs absolute using the source base URL
    if (url.startsWith('/') && source.baseUrl) {
      url = source.baseUrl + url;
    }

    const rawDesc = getTextContent(node, ['description', 'summary', 'content\\:encoded', 'content']);
    const summary = stripHTML(rawDesc).slice(0, 280);
    const dateStr = getTextContent(node, ['pubDate', 'published', 'updated', 'dc\\:date']);
    const date    = dateStr ? new Date(dateStr) : null;
    const image   = findImage(node);
    const category = assignCategory(title, summary);

    articles.push({
      id:          url,
      title,
      url,
      summary,
      publishedAt: date && !isNaN(date) ? date : null,
      sourceId:    source.id,
      sourceName:  source.name,
      sourceColor: source.color,
      sourceIcon:  source.icon,
      category,
      image,
    });
  }
  return articles.slice(0, MAX_ARTICLES_PER_SOURCE);
}

async function fetchSource(source) {
  for (const feedUrl of source.feedUrls) {
    try {
      const text = await fetchViaProxy(feedUrl);
      const doc  = parseXML(text);
      const arts = parseEntries(doc, source);
      if (arts.length > 0) return { articles: arts, error: null };
    } catch (e) {
      console.warn(`${source.name} — feed mislukt (${feedUrl}):`, e.message);
    }
  }
  return { articles: [], error: `Kon geen feed ophalen van ${source.name}` };
}

// ============================================================
// CACHING
// ============================================================

function saveCache(articles) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      articles: articles.map(a => ({ ...a, publishedAt: a.publishedAt?.toISOString() ?? null })),
      fetchedAt: Date.now(),
    }));
  } catch (_) {}
}

function loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { articles, fetchedAt } = JSON.parse(raw);
    return {
      articles: articles.map(a => ({ ...a, publishedAt: a.publishedAt ? new Date(a.publishedAt) : null })),
      fetchedAt,
    };
  } catch (_) {
    return null;
  }
}

// ============================================================
// FETCH ALL
// ============================================================

async function fetchAll(force = false) {
  // Check cache first
  if (!force) {
    const cached = loadCache();
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL) {
      allArticles = cached.articles;
      lastFetched = new Date(cached.fetchedAt);
      render();
      updateUpdateBadge();
      showState('articles');
      return;
    }
  }

  showState('loading');

  const results = await Promise.allSettled(SOURCES.map(fetchSource));
  const errors  = [];
  const fetched = [];

  results.forEach((r, i) => {
    if (r.status === 'fulfilled') {
      fetched.push(...r.value.articles);
      if (r.value.error) errors.push(r.value.error);
    } else {
      errors.push(`${SOURCES[i].name}: ${r.reason?.message}`);
    }
  });

  // Deduplicate by URL
  const seen = new Set();
  allArticles = fetched.filter(a => {
    if (seen.has(a.url)) return false;
    seen.add(a.url);
    return true;
  });

  // Sort newest first (nulls last)
  allArticles.sort((a, b) => {
    if (!a.publishedAt && !b.publishedAt) return 0;
    if (!a.publishedAt) return 1;
    if (!b.publishedAt) return -1;
    return b.publishedAt - a.publishedAt;
  });

  lastFetched = new Date();
  saveCache(allArticles);

  if (errors.length) {
    document.getElementById('error-detail').innerHTML =
      errors.map(e => `<div>• ${e}</div>`).join('');
    showState('error');
  }

  render();
  updateUpdateBadge();
  if (allArticles.length > 0) showState('articles');
}

// ============================================================
// FILTERING
// ============================================================

function getFiltered() {
  const q = searchQuery.toLowerCase();
  return allArticles.filter(a => {
    if (activeCategory !== 'Alle' && a.category !== activeCategory) return false;
    if (activeSource && a.sourceId !== activeSource) return false;
    if (q && !a.title.toLowerCase().includes(q) && !a.summary.toLowerCase().includes(q)) return false;
    return true;
  });
}

// ============================================================
// RENDERING
// ============================================================

function formatDate(date) {
  if (!date) return '';
  const months = ['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec'];
  return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

function categorySlug(cat) {
  return cat.toLowerCase().replace(/\s*&\s*/g, '-').replace(/\s+/g, '-');
}

function renderCategoryBar() {
  const bar = document.getElementById('category-bar');

  // Remove existing category pills (keep the "Alle" pill)
  bar.querySelectorAll('[data-category]:not([data-category="Alle"])').forEach(el => el.remove());

  // Count per category
  const counts = {};
  allArticles.forEach(a => { counts[a.category] = (counts[a.category] || 0) + 1; });

  // Total
  const total = getFilteredBySourceAndSearch().length;
  document.getElementById('count-alle').textContent = total;

  for (const [cat, keywords] of Object.entries(CATEGORIES)) {
    const cnt = allArticles.filter(a => {
      if (activeSource && a.sourceId !== activeSource) return false;
      const q = searchQuery.toLowerCase();
      if (q && !a.title.toLowerCase().includes(q) && !a.summary.toLowerCase().includes(q)) return false;
      return a.category === cat;
    }).length;
    if (cnt === 0) continue;

    const icon = CAT_ICONS[cat] || 'bi-tag';
    const pill = document.createElement('button');
    pill.className = `category-pill cat-${categorySlug(cat)}` + (activeCategory === cat ? ' active' : '');
    pill.dataset.category = cat;
    pill.innerHTML = `<i class="bi ${icon}"></i> ${cat} <span class="count">${cnt}</span>`;
    pill.addEventListener('click', () => {
      activeCategory = cat;
      render();
    });
    bar.appendChild(pill);
  }

  // Update "Alle" pill active state
  bar.querySelector('[data-category="Alle"]')
    .classList.toggle('active', activeCategory === 'Alle');
}

function getFilteredBySourceAndSearch() {
  const q = searchQuery.toLowerCase();
  return allArticles.filter(a => {
    if (activeSource && a.sourceId !== activeSource) return false;
    if (q && !a.title.toLowerCase().includes(q) && !a.summary.toLowerCase().includes(q)) return false;
    return true;
  });
}

function renderSourceBar() {
  const bar = document.getElementById('source-bar');
  bar.innerHTML = '';

  SOURCES.forEach(src => {
    const count = allArticles.filter(a => a.sourceId === src.id).length;
    if (count === 0) return;

    const btn = document.createElement('button');
    const isActive = activeSource === src.id;
    btn.className = `source-filter-btn ${isActive ? 'active' : ''}`;
    btn.style.setProperty('--src-color', src.color);
    btn.innerHTML = `<i class="bi ${src.icon}"></i> ${src.name} <span class="badge ms-1">${count}</span>`;
    btn.addEventListener('click', () => {
      activeSource = isActive ? null : src.id;
      render();
    });
    bar.appendChild(btn);
  });

  // Footer sources
  const footer = document.getElementById('footer-sources');
  footer.innerHTML = '<span class="text-muted small fw-semibold">Bronnen:</span>';
  SOURCES.forEach(src => {
    footer.innerHTML += `<a href="${src.feedUrls[0]}" target="_blank" rel="noopener"
      class="source-badge text-decoration-none small" style="--src-color:${src.color}">
      <i class="bi ${src.icon}"></i> ${src.name}
    </a>`;
  });
}

function renderArticles(articles) {
  const grid = document.getElementById('articles-grid');
  grid.innerHTML = '';

  if (articles.length === 0) {
    showState('empty');
    return;
  }
  showState('articles');

  document.getElementById('results-count').textContent =
    `${articles.length} artikel${articles.length !== 1 ? 'en' : ''}`;

  articles.forEach(a => {
    const col  = document.createElement('div');
    col.className = 'col-md-6 col-xl-4';

    const slug = categorySlug(a.category);
    const imgHtml = a.image
      ? `<div class="news-card-img"><img src="${a.image}" alt="" loading="lazy" onerror="this.closest('.news-card-img').remove()"></div>`
      : '';
    const dateHtml = a.publishedAt
      ? `<span class="ms-auto text-muted small">${formatDate(a.publishedAt)}</span>`
      : '';
    const summaryHtml = a.summary
      ? `<p class="news-summary text-muted">${a.summary}</p>`
      : '';

    col.innerHTML = `
      <article class="news-card h-100">
        ${imgHtml}
        <div class="news-card-body">
          <div class="d-flex align-items-center gap-2 mb-2 flex-wrap">
            <span class="source-badge-sm" style="--src-color:${a.sourceColor}">
              <i class="bi ${a.sourceIcon}"></i> ${a.sourceName}
            </span>
            <span class="category-tag cat-${slug}">${a.category}</span>
            ${dateHtml}
          </div>
          <h2 class="news-title">
            <a href="${a.url}" target="_blank" rel="noopener noreferrer"
               class="stretched-link text-decoration-none text-dark">${a.title}</a>
          </h2>
          ${summaryHtml}
        </div>
        <div class="news-card-footer">
          <a href="${a.url}" target="_blank" rel="noopener noreferrer" class="btn-read-more">
            Lees verder <i class="bi bi-arrow-right"></i>
          </a>
        </div>
      </article>`;
    grid.appendChild(col);
  });
}

function render() {
  renderCategoryBar();
  renderSourceBar();
  renderArticles(getFiltered());
}

// ============================================================
// UI STATE MANAGEMENT
// ============================================================

function showState(state) {
  document.getElementById('loading-state').classList.toggle('d-none', state !== 'loading');
  document.getElementById('articles-grid').classList.toggle('d-none', state !== 'articles');
  document.getElementById('empty-state').classList.toggle('d-none', state !== 'empty');
  // Keep error visible alongside articles if there was a partial failure
  if (state !== 'error') {
    // only hide if we have articles (partial success)
    if (state === 'articles') document.getElementById('error-state').classList.add('d-none');
  } else {
    document.getElementById('error-state').classList.remove('d-none');
  }
}

// ============================================================
// UPDATE BADGE
// ============================================================

function updateUpdateBadge() {
  if (!lastFetched) return;
  const badge = document.getElementById('update-badge');
  const span  = document.getElementById('update-time');
  badge.style.removeProperty('display');
  badge.classList.remove('d-none');

  const diffMin = Math.floor((Date.now() - lastFetched) / 60000);
  if (diffMin < 1)       span.textContent = 'zojuist';
  else if (diffMin < 60) span.textContent = `${diffMin} min geleden`;
  else                   span.textContent = `${Math.floor(diffMin/60)}u geleden`;

  // Update every minute
  setTimeout(updateUpdateBadge, 60000);
}

// ============================================================
// TOAST
// ============================================================

function showToast(msg, type = 'info') {
  const icons = { success: 'check-circle-fill', danger: 'x-circle-fill', info: 'info-circle-fill' };
  const id  = 'toast-' + Date.now();
  document.getElementById('toast-container').insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi bi-${icons[type]||'info-circle-fill'}"></i>${msg}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`);
  const el = document.getElementById(id);
  new bootstrap.Toast(el, { delay: 4000 }).show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ============================================================
// REFRESH
// ============================================================

async function triggerRefresh() {
  const btn  = document.getElementById('refresh-btn');
  const icon = document.getElementById('refresh-icon');
  btn.disabled = true;
  icon.classList.add('spin');
  try {
    const before = allArticles.length;
    await fetchAll(true);
    const newCount = allArticles.length - before;
    if (newCount > 0)
      showToast(`${newCount} nieuw artikel${newCount !== 1 ? 'en' : ''} opgehaald!`, 'success');
    else
      showToast('Geen nieuwe artikelen gevonden.', 'info');
  } finally {
    btn.disabled = false;
    icon.classList.remove('spin');
  }
}

// ============================================================
// INIT
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  // Alle pill click
  document.querySelector('[data-category="Alle"]').addEventListener('click', () => {
    activeCategory = 'Alle';
    render();
  });

  // Search
  const searchInput = document.getElementById('search-input');
  document.getElementById('search-btn').addEventListener('click', () => {
    searchQuery = searchInput.value.trim();
    render();
  });
  searchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { searchQuery = searchInput.value.trim(); render(); }
  });
  searchInput.addEventListener('input', () => {
    if (!searchInput.value) { searchQuery = ''; render(); }
  });

  // Refresh button
  document.getElementById('refresh-btn').addEventListener('click', triggerRefresh);
  document.getElementById('retry-btn')?.addEventListener('click', () => fetchAll(true));

  // Clear filters
  document.getElementById('clear-filter-btn')?.addEventListener('click', () => {
    activeCategory = 'Alle';
    activeSource   = null;
    searchQuery    = '';
    searchInput.value = '';
    render();
  });

  // Auto-refresh
  refreshTimer = setInterval(() => fetchAll(false), AUTO_REFRESH);

  // Initial load
  fetchAll(false);
});
