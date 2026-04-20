SOURCES = [
    {
        'id': 'bnetwerk',
        'name': 'Bnetwerk',
        'base_url': 'https://www.bibliotheeknetwerk.nl',
        'feed_urls': [
            'https://www.bibliotheeknetwerk.nl/rss.xml',
            'https://www.bibliotheeknetwerk.nl/feed',
            'https://www.bibliotheeknetwerk.nl/nieuws/rss.xml',
            'https://www.bibliotheeknetwerk.nl/nieuws/feed',
        ],
        'scrape_url': 'https://www.bibliotheeknetwerk.nl/nieuws',
        'color': '#1565c0',
        'icon': 'bi-building',
    },
    {
        'id': 'markdekkers',
        'name': 'Mark Dekkers',
        'base_url': 'https://www.markdeckers.net',
        'feed_urls': [
            'https://www.markdeckers.net/feeds/posts/default?alt=rss',
            'https://www.markdeckers.net/feeds/posts/default',
            'https://www.markdeckers.net/atom.xml',
            'https://www.markdeckers.net/rss.xml',
        ],
        'scrape_url': 'https://www.markdeckers.net/',
        'color': '#e65100',
        'icon': 'bi-pencil-square',
    },
    {
        'id': 'bibliotheekblad',
        'name': 'Bibliotheekblad',
        'base_url': 'https://bibliotheekblad.nl',
        'feed_urls': [
            'https://bibliotheekblad.nl/feed/',
            'https://bibliotheekblad.nl/rss',
            'https://bibliotheekblad.nl/feed',
        ],
        'scrape_url': 'https://bibliotheekblad.nl',
        'color': '#2e7d32',
        'icon': 'bi-newspaper',
    },
]

CATEGORIES = {
    'Digitaal': [
        'digitaal', 'e-book', 'ebook', 'digitale bibliotheek', 'app', 'online',
        'streaming', 'e-reader', 'epub', 'luisterboek', 'platform', 'uitlenen online',
        'digitalisering', 'website', 'e-content',
    ],
    'Beleid': [
        'beleid', 'wet', 'subsidie', 'financiering', 'budget', 'overheid',
        'ministerie', 'gemeente', 'wethouder', 'bezuiniging', 'politiek',
        'bibliotheekwet', 'stelsel', 'ocw', 'rijksoverheid',
    ],
    'Lezen & Educatie': [
        'lezen', 'onderwijs', 'jeugd', 'kinderen', 'school', 'laaggeletterdheid',
        'educatie', 'voorlezen', 'leesbevordering', 'taalvaardigheid', 'taalcoach',
        'leescafé', 'nationale voorleesdagen', 'leesclubs', 'leesplezier',
        'alfabetisering', 'nt2', 'geletterdheid',
    ],
    'Statistieken': [
        'statistieken', 'cijfers', 'rapport', 'onderzoek', 'data', 'meting',
        'uitleningen', 'gebruik', 'bezoekers', 'percentage', 'groei',
        'jaarverslag', 'monitor', 'analyse', 'trend',
    ],
    'Innovatie': [
        'innovatie', 'technologie', 'ai', 'artificial intelligence', 'automatisering',
        'robot', 'chatbot', 'machine learning', 'smart', 'experiment',
        'pilot', 'nieuw concept', 'makerspace',
    ],
    'Collectie': [
        'collectie', 'aanwinsten', 'muziek', 'film', 'boeken', 'tijdschriften',
        'stripboek', 'magazine', 'dvd', 'nbd biblion', 'selectie', 'titel',
        'prentenboek', 'non-fictie', 'fictie',
    ],
    'Organisatie': [
        'personeel', 'bestuur', 'directie', 'samenwerking', 'fusie', 'verbouwing',
        'opening', 'sluiting', 'directeur', 'medewerker', 'vrijwilliger',
        'reorganisatie', 'gebouw', 'nieuwbouw', 'verhuizing',
    ],
    'Evenementen': [
        'evenement', 'congres', 'conferentie', 'lezing', 'workshop', 'festival',
        'tentoonstelling', 'bijeenkomst', 'symposium', 'dag van', 'manifestatie',
        'activiteit', 'programma', 'themaweek',
    ],
}

UPDATE_INTERVAL_MINUTES = 60
MAX_ARTICLES_PER_SOURCE = 50
DB_PATH = 'nieuws.db'
