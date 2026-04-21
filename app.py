import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from config import CATEGORIES, SOURCES, UPDATE_INTERVAL_MINUTES
from database import (
    get_actieve_peilingen,
    get_articles,
    get_category_counts,
    get_last_update,
    get_peiling,
    get_source_statuses,
    get_total_count,
    get_uitslag,
    init_db,
    init_peiling_tables,
    maak_peiling,
    sla_antwoord_op,
)
from scraper import fetch_all_sources

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(name)-20s  %(levelname)s  %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Source lookup by id
SOURCE_MAP = {s['id']: s for s in SOURCES}


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

@app.template_filter('datetimeformat')
def datetimeformat(value, fmt='%-d %b %Y'):
    if not value:
        return ''
    from datetime import datetime
    try:
        if isinstance(value, str):
            from dateutil import parser as dp
            dt = dp.parse(value)
        else:
            dt = value
        # Dutch month abbreviations
        months = {
            1: 'jan', 2: 'feb', 3: 'mrt', 4: 'apr', 5: 'mei', 6: 'jun',
            7: 'jul', 8: 'aug', 9: 'sep', 10: 'okt', 11: 'nov', 12: 'dec',
        }
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except Exception:
        return str(value)[:10]


CAT_ICONS = {
    'Digitaal': 'bi-laptop',
    'Beleid': 'bi-bank2',
    'Lezen & Educatie': 'bi-book-open',
    'Statistieken': 'bi-bar-chart-line',
    'Innovatie': 'bi-lightbulb',
    'Collectie': 'bi-collection',
    'Organisatie': 'bi-people',
    'Evenementen': 'bi-calendar-event',
    'Overig': 'bi-tag',
}


@app.template_global()
def cat_icon(category: str) -> str:
    from markupsafe import Markup
    icon = CAT_ICONS.get(category, 'bi-tag')
    return Markup(f'<i class="bi {icon}"></i>')


@app.context_processor
def inject_globals():
    return {
        'source_map': SOURCE_MAP,
        'all_categories': list(CATEGORIES.keys()),
        'sources': SOURCES,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    category = request.args.get('category', 'Alle')
    source_id = request.args.get('source', '')
    search = request.args.get('q', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 24
    offset = (page - 1) * per_page

    cat_filter = category if category != 'Alle' else None
    src_filter = source_id or None
    srch_filter = search or None

    articles = get_articles(
        category=cat_filter,
        source_id=src_filter,
        search=srch_filter,
        limit=per_page,
        offset=offset,
    )
    total = get_total_count(category=cat_filter, source_id=src_filter, search=srch_filter)
    category_counts = get_category_counts()
    source_statuses = get_source_statuses()
    last_update = get_last_update()
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Total count per category including 'Alle'
    all_count = get_total_count()

    return render_template(
        'index.html',
        articles=articles,
        category_counts=category_counts,
        all_count=all_count,
        selected_category=category,
        selected_source=source_id,
        search=search,
        source_statuses=source_statuses,
        last_update=last_update,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page,
    )


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    try:
        saved = fetch_all_sources()
        last = get_last_update()
        return jsonify({'status': 'ok', 'new_articles': saved, 'last_update': last})
    except Exception as e:
        logger.exception("Refresh failed")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/articles')
def api_articles():
    category = request.args.get('category') or None
    source_id = request.args.get('source') or None
    search = request.args.get('q') or None
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))

    articles = get_articles(category=category, source_id=source_id, search=search,
                            limit=limit, offset=offset)
    total = get_total_count(category=category, source_id=source_id, search=search)
    return jsonify({'articles': articles, 'total': total, 'offset': offset, 'limit': limit})


@app.route('/api/status')
def api_status():
    return jsonify({
        'sources': get_source_statuses(),
        'last_update': get_last_update(),
        'total_articles': get_total_count(),
    })


# ---------------------------------------------------------------------------
# Peilingen — anonieme stemmingen voor Koffieuurtje-sessies
# ---------------------------------------------------------------------------

@app.route('/peiling/<int:peiling_id>')
def peiling(peiling_id):
    data = get_peiling(peiling_id)
    if not data:
        abort(404)
    return render_template('peiling.html', **data)


@app.route('/peiling/<int:peiling_id>/stem', methods=['POST'])
def stem(peiling_id):
    optie_id = request.form.get('optie_id', type=int)
    if not optie_id:
        return redirect(url_for('peiling', peiling_id=peiling_id))
    # Sla anoniem antwoord op — geen persoonsgegevens worden geregistreerd
    sla_antwoord_op(peiling_id, optie_id)
    return redirect(url_for('uitslag', peiling_id=peiling_id))


@app.route('/peiling/<int:peiling_id>/uitslag')
def uitslag(peiling_id):
    data = get_uitslag(peiling_id)
    if not data:
        abort(404)
    return render_template('uitslag.html', **data)


@app.route('/api/peiling', methods=['POST'])
def api_maak_peiling():
    body = request.get_json(silent=True) or {}
    vraag = (body.get('vraag') or '').strip()
    opties = [o.strip() for o in body.get('opties', []) if str(o).strip()]
    if not vraag or len(opties) < 2:
        return jsonify({'status': 'error', 'message': 'Geef een vraag en minimaal 2 opties op.'}), 400
    peiling_id = maak_peiling(vraag, opties)
    return jsonify({'status': 'ok', 'peiling_id': peiling_id,
                    'url': url_for('peiling', peiling_id=peiling_id, _external=True)}), 201


@app.route('/peilingen')
def peilingen_overzicht():
    peilingen = get_actieve_peilingen()
    return render_template('peilingen.html', peilingen=peilingen)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def start_scheduler():
    scheduler = BackgroundScheduler(timezone='Europe/Amsterdam')
    scheduler.add_job(
        func=fetch_all_sources,
        trigger='interval',
        minutes=UPDATE_INTERVAL_MINUTES,
        id='fetch_news',
        name='Fetch library news',
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    logger.info(f"Scheduler gestart — update elke {UPDATE_INTERVAL_MINUTES} minuten")
    return scheduler


if __name__ == '__main__':
    init_db()
    init_peiling_tables()
    logger.info("Eerste nieuwsophaling gestart…")
    fetch_all_sources()
    start_scheduler()
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
