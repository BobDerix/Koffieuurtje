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


# ---------------------------------------------------------------------------
# Peilingen (anonieme stemmingen voor Koffieuurtje-sessies)
# ---------------------------------------------------------------------------

def init_peiling_tables():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS peilingen (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            vraag       TEXT NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_actief   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS peiling_opties (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            peiling_id  INTEGER NOT NULL REFERENCES peilingen(id),
            optie_tekst TEXT NOT NULL,
            volgorde    INTEGER DEFAULT 0
        );

        -- Geen persoonsgegevens: geen IP, geen sessie-ID, geen gebruiker.
        -- Antwoorden zijn nooit te herleiden tot een persoon.
        CREATE TABLE IF NOT EXISTS peiling_antwoorden (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            peiling_id  INTEGER NOT NULL REFERENCES peilingen(id),
            optie_id    INTEGER NOT NULL REFERENCES peiling_opties(id),
            ingediend_op DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()


def maak_peiling(vraag: str, opties: list[str]) -> int:
    conn = get_db()
    cur = conn.execute('INSERT INTO peilingen (vraag) VALUES (?)', (vraag,))
    peiling_id = cur.lastrowid
    for i, tekst in enumerate(opties):
        conn.execute(
            'INSERT INTO peiling_opties (peiling_id, optie_tekst, volgorde) VALUES (?, ?, ?)',
            (peiling_id, tekst, i),
        )
    conn.commit()
    conn.close()
    return peiling_id


def get_peiling(peiling_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute('SELECT * FROM peilingen WHERE id = ?', (peiling_id,)).fetchone()
    if not row:
        conn.close()
        return None
    opties = conn.execute(
        'SELECT * FROM peiling_opties WHERE peiling_id = ? ORDER BY volgorde',
        (peiling_id,),
    ).fetchall()
    conn.close()
    return {'peiling': dict(row), 'opties': [dict(o) for o in opties]}


def sla_antwoord_op(peiling_id: int, optie_id: int) -> bool:
    """Sla een anoniem antwoord op. Geen persoonsgegevens worden geregistreerd."""
    conn = get_db()
    # Controleer dat optie bij deze peiling hoort
    row = conn.execute(
        'SELECT id FROM peiling_opties WHERE id = ? AND peiling_id = ?',
        (optie_id, peiling_id),
    ).fetchone()
    if not row:
        conn.close()
        return False
    conn.execute(
        'INSERT INTO peiling_antwoorden (peiling_id, optie_id) VALUES (?, ?)',
        (peiling_id, optie_id),
    )
    conn.commit()
    conn.close()
    return True


def get_uitslag(peiling_id: int) -> dict | None:
    conn = get_db()
    peiling = conn.execute('SELECT * FROM peilingen WHERE id = ?', (peiling_id,)).fetchone()
    if not peiling:
        conn.close()
        return None
    opties = conn.execute(
        'SELECT * FROM peiling_opties WHERE peiling_id = ? ORDER BY volgorde',
        (peiling_id,),
    ).fetchall()
    totaal = conn.execute(
        'SELECT COUNT(*) FROM peiling_antwoorden WHERE peiling_id = ?',
        (peiling_id,),
    ).fetchone()[0]
    resultaten = []
    for optie in opties:
        aantal = conn.execute(
            'SELECT COUNT(*) FROM peiling_antwoorden WHERE optie_id = ?',
            (optie['id'],),
        ).fetchone()[0]
        resultaten.append({
            'optie_id': optie['id'],
            'optie_tekst': optie['optie_tekst'],
            'aantal': aantal,
            'percentage': round(aantal / totaal * 100) if totaal else 0,
        })
    conn.close()
    return {'peiling': dict(peiling), 'resultaten': resultaten, 'totaal': totaal}


def get_actieve_peilingen() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM peilingen WHERE is_actief = 1 ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
