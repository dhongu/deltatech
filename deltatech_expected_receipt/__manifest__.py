# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Expected Receipts",
    "summary": "Card payments registered when received, settled against the grouped bank transfer to the cent",
    "version": "19.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Accounting/Accounting",
    "depends": ["account", "sale"],
    "license": "OPL-1",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/expected_receipt_views.xml",
        "views/card_terminal_views.xml",
        "wizard/card_payment_views.xml",
        "wizard/card_settlement_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/menus.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
    "price": 200.0,
    "currency": "EUR",
}
