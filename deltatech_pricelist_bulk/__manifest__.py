# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
{
    "name": "Pricelist Bulk Rules",
    "summary": "Add pricelist rules for many products at once and apply the same formula to many rules",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["product"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "wizard/pricelist_bulk_add_views.xml",
        "wizard/pricelist_bulk_formula_views.xml",
        "views/product_pricelist_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
