{
    "name": "Many2one Badge Widget",
    "version": "18.0.1.0.0",
    "category": "Web",
    "summary": "Many2one field widget displayed as colored badge, similar to many2many_tags",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "deltatech_widget_many2one_badge/static/src/css/many2one_badge_field.css",
            "deltatech_widget_many2one_badge/static/src/js/many2one_badge_field.esm.js",
            "deltatech_widget_many2one_badge/static/src/xml/many2one_badge_field.xml",
        ],
        "web.assets_unit_tests": [
            "deltatech_widget_many2one_badge/static/tests/many2one_badge_field.test.esm.js",
        ],
    },
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
