# © 2025 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Competitors Price",
    "summary": "Track competitors' product prices and fetch on demand",
    "version": "18.0.1.0.0",
    "category": "Product",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": ["product"],
    "external_dependencies": {"python": ["extruct", "w3lib"]},
    "data": [
        "security/ir.model.access.csv",
        "views/competitor_price_views.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
    "installable": True,
}
