{
    "name": "Deltatech Website Blocks",
    "summary": "Custom website building blocks",
    "version": "18.0.1.0.0",
    "category": "Website/Website",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": [
        "website",
    ],
    "data": [
        "views/snippets/s_partners_loop.xml",
        "views/snippets/s_stats_counters.xml",
        "views/snippets/s_cards_grid.xml",
        "views/snippets/s_deltatech_special_products.xml",
        "views/snippets/snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_blocks/static/src/snippets/s_partners_loop/000.scss",
            "deltatech_website_blocks/static/src/snippets/s_partners_loop/000.js",
            "deltatech_website_blocks/static/src/snippets/s_stats_counters/000.scss",
            "deltatech_website_blocks/static/src/snippets/s_stats_counters/000.js",
            "deltatech_website_blocks/static/src/snippets/s_cards_grid/000.scss",
            "deltatech_website_blocks/static/src/snippets/s_deltatech_special_products/000.scss",
            "deltatech_website_blocks/static/src/snippets/s_deltatech_special_products/000.js",
        ],
        "website.assets_wysiwyg": [
            "deltatech_website_blocks/static/src/snippets/s_partners_loop/options.js",
            "deltatech_website_blocks/static/src/snippets/s_stats_counters/options.js",
        ],
    },
    "installable": True,
    "maintainers": ["VoicuStefan2001"],
    "development_status": "Alpha",
}
