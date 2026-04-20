import sqlite3
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            url         TEXT UNIQUE NOT NULL,
            summary     TEXT,
            published_at DATETIME,
            fetched_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_id   TEXT NOT NULL,
            source_name TEXT NOT NULL,
            category    TEXT DEFAULT 'Overig',
            image_url   TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
        CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id);
        CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);

        CREATE TABLE IF NOT EXISTS source_status (
            source_id       TEXT PRIMARY KEY,
            last_updated    DATETIME,
            last_error      TEXT,
            article_count   INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    conn.close()


def save_articles(articles):
    conn = get_db()
    saved = 0
    for article in articles:
        try:
            conn.execute(
                '''INSERT OR IGNORE INTO articles
                   (title, url, summary, published_at, source_id, source_name, category, image_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    article['title'],
                    article['url'],
                    article.get('summary'),
                    article.get('published_at'),
                    article['source_id'],
                    article['source_name'],
                    article.get('category', 'Overig'),
                    article.get('image_url'),
                ),
            )
            if conn.execute('SELECT changes()').fetchone()[0]:
                saved += 1
        except Exception as e:
            print(f"Error saving article '{article.get('title', '')}': {e}")
    conn.commit()
    conn.close()
    return saved


def get_articles(category=None, source_id=None, search=None, limit=24, offset=0):
    conn = get_db()
    query = 'SELECT * FROM articles WHERE 1=1'
    params = []

    if category and category != 'Alle':
        query += ' AND category = ?'
        params.append(category)

    if source_id:
        query += ' AND source_id = ?'
        params.append(source_id)

    if search:
        query += ' AND (title LIKE ? OR summary LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    query += ' ORDER BY published_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_count(category=None, source_id=None, search=None):
    conn = get_db()
    query = 'SELECT COUNT(*) FROM articles WHERE 1=1'
    params = []

    if category and category != 'Alle':
        query += ' AND category = ?'
        params.append(category)

    if source_id:
        query += ' AND source_id = ?'
        params.append(source_id)

    if search:
        query += ' AND (title LIKE ? OR summary LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    count = conn.execute(query, params).fetchone()[0]
    conn.close()
    return count


def get_category_counts():
    conn = get_db()
    rows = conn.execute(
        'SELECT category, COUNT(*) as cnt FROM articles GROUP BY category ORDER BY cnt DESC'
    ).fetchall()
    conn.close()
    return {r['category']: r['cnt'] for r in rows}


def update_source_status(source_id, error=None, count=0):
    conn = get_db()
    conn.execute(
        '''INSERT OR REPLACE INTO source_status (source_id, last_updated, last_error, article_count)
           VALUES (?, CURRENT_TIMESTAMP, ?, ?)''',
        (source_id, error, count),
    )
    conn.commit()
    conn.close()


def get_source_statuses():
    conn = get_db()
    rows = conn.execute('SELECT * FROM source_status').fetchall()
    conn.close()
    return {r['source_id']: dict(r) for r in rows}


def get_last_update():
    conn = get_db()
    row = conn.execute('SELECT MAX(fetched_at) AS t FROM articles').fetchone()
    conn.close()
    return row['t'] if row else None
