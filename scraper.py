import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from config import CATEGORIES, MAX_ARTICLES_PER_SOURCE, SOURCES

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assign_category(title: str, summary: str = '') -> str:
    text = (title + ' ' + (summary or '')).lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                return category
    return 'Overig'


def parse_date(value) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return dateparser.parse(str(value)).isoformat()
    except Exception:
        return None


def clean_html(html: str) -> str:
    if not html:
        return ''
    text = BeautifulSoup(html, 'html.parser').get_text(separator=' ')
    return ' '.join(text.split())[:600]


def get_image_from_entry(entry) -> str | None:
    for attr in ('media_content', 'media_thumbnail'):
        items = getattr(entry, attr, None)
        if items:
            return items[0].get('url')
    for enc in getattr(entry, 'enclosures', []):
        if enc.get('type', '').startswith('image/'):
            return enc.get('href') or enc.get('url')
    # Try content for <img> tags
    for content_item in getattr(entry, 'content', []):
        soup = BeautifulSoup(content_item.get('value', ''), 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img['src']
    # Check summary for img
    summary_html = entry.get('summary', '')
    if summary_html:
        soup = BeautifulSoup(summary_html, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img['src']
    return None


# ---------------------------------------------------------------------------
# RSS / Atom fetching
# ---------------------------------------------------------------------------

def fetch_rss(source: dict, feed_url: str) -> list | None:
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        if not feed.entries:
            return None

        articles = []
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            title = (entry.get('title') or '').strip()
            url = (entry.get('link') or '').strip()
            if not title or not url:
                continue

            summary = clean_html(entry.get('summary') or entry.get('description') or '')
            published = None
            for attr in ('published', 'updated', 'created'):
                val = entry.get(attr)
                if val:
                    published = parse_date(val)
                    break
            image_url = get_image_from_entry(entry)
            category = assign_category(title, summary)

            articles.append({
                'title': title,
                'url': url,
                'summary': summary,
                'published_at': published,
                'source_id': source['id'],
                'source_name': source['name'],
                'category': category,
                'image_url': image_url,
            })

        return articles if articles else None
    except Exception as e:
        logger.warning(f"RSS fetch failed for {feed_url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Site-specific scrapers (fallback when RSS unavailable / blocked)
# ---------------------------------------------------------------------------

def scrape_bnetwerk(source: dict) -> list | None:
    try:
        resp = requests.get(source['scrape_url'], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        articles = []
        seen = set()

        # Drupal-style views: article cards often have h2/h3 with links
        for heading in soup.find_all(['h2', 'h3']):
            link = heading.find('a', href=True)
            if not link:
                continue
            href = link['href']
            title = link.get_text(strip=True)
            if not title or href in seen:
                continue
            # Only internal content links (articles)
            if not any(p in href for p in ['/artikel/', '/nieuws/', '/blog/']):
                continue

            full_url = urljoin(source['base_url'], href)
            seen.add(href)

            # Try to get summary from sibling/parent text
            parent = heading.parent
            summary = ''
            if parent:
                p = parent.find('p')
                if p:
                    summary = p.get_text(separator=' ', strip=True)[:600]

            # Try to get date
            date_el = parent.find(['time', 'span'], class_=lambda c: c and 'date' in c.lower()) if parent else None
            published = parse_date(date_el.get('datetime') or date_el.get_text() if date_el else None)

            articles.append({
                'title': title,
                'url': full_url,
                'summary': summary,
                'published_at': published,
                'source_id': source['id'],
                'source_name': source['name'],
                'category': assign_category(title, summary),
                'image_url': None,
            })
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

        return articles if articles else None
    except Exception as e:
        logger.error(f"Scraping failed for {source['name']}: {e}")
        return None


def scrape_markdekkers(source: dict) -> list | None:
    try:
        resp = requests.get(source['scrape_url'], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        articles = []
        seen = set()

        # Blogger: posts are in .post or article elements
        for post in soup.select('.post, article, .blog-post, .hentry'):
            title_el = post.select_one('h2 a, h3 a, .post-title a, .entry-title a')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get('href', '')
            if not url or url in seen:
                continue
            seen.add(url)

            body_el = post.select_one('.post-body, .entry-content')
            summary = clean_html(str(body_el))[:600] if body_el else ''

            date_el = post.select_one('.date-header, .post-timestamp time, time[datetime], .published')
            published = parse_date(
                date_el.get('datetime') or date_el.get_text() if date_el else None
            )

            img = post.find('img')
            image_url = img['src'] if img and img.get('src') else None

            articles.append({
                'title': title,
                'url': url,
                'summary': summary,
                'published_at': published,
                'source_id': source['id'],
                'source_name': source['name'],
                'category': assign_category(title, summary),
                'image_url': image_url,
            })
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

        return articles if articles else None
    except Exception as e:
        logger.error(f"Scraping failed for {source['name']}: {e}")
        return None


def scrape_generic(source: dict) -> list | None:
    """Generic scraper for blog/news sites."""
    try:
        resp = requests.get(source['scrape_url'], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        articles = []
        seen = set()
        base = source['base_url']

        for tag in soup.find_all(['h1', 'h2', 'h3']):
            link = tag.find('a', href=True)
            if not link:
                continue
            title = link.get_text(strip=True)
            href = link['href']
            if not title or len(title) < 15 or href in seen:
                continue
            seen.add(href)
            full_url = urljoin(base, href)

            articles.append({
                'title': title,
                'url': full_url,
                'summary': '',
                'published_at': None,
                'source_id': source['id'],
                'source_name': source['name'],
                'category': assign_category(title),
                'image_url': None,
            })
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

        return articles if articles else None
    except Exception as e:
        logger.error(f"Generic scraping failed for {source['name']}: {e}")
        return None


SCRAPERS = {
    'bnetwerk': scrape_bnetwerk,
    'markdekkers': scrape_markdekkers,
    'bibliotheekblad': scrape_generic,
}


# ---------------------------------------------------------------------------
# Main fetch logic
# ---------------------------------------------------------------------------

def fetch_source(source: dict) -> tuple[list, str | None]:
    # Try RSS first
    for feed_url in source.get('feed_urls', []):
        articles = fetch_rss(source, feed_url)
        if articles:
            logger.info(f"{source['name']}: {len(articles)} articles via RSS ({feed_url})")
            return articles, None

    # Fall back to scraping
    scraper = SCRAPERS.get(source['id'], scrape_generic)
    articles = scraper(source)
    if articles:
        logger.info(f"{source['name']}: {len(articles)} articles via scraping")
        return articles, None

    error = f"Kon geen artikelen ophalen van {source['name']}"
    logger.error(error)
    return [], error


def fetch_all_sources() -> int:
    from database import save_articles, update_source_status

    total_saved = 0
    for source in SOURCES:
        articles, error = fetch_source(source)
        saved = save_articles(articles) if articles else 0
        total_saved += saved
        update_source_status(source['id'], error=error, count=len(articles))
        logger.info(f"{source['name']}: {saved} nieuwe artikelen opgeslagen")

    return total_saved
