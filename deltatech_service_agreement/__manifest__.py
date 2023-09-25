# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Services Agreement",
    "summary": "Manage Services Agreement",
    "version": "16.0.2.0.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Agreement",
    "depends": [
        "base",
        "product",
        "account",
        # "date_range",
        "deltatech_service_base",
        # "deltatech_agreement_management",
    ],
    "license": "OPL-1",
    "data": [
        "security/service_security.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/service_consumption_view.xml",
        "views/service_agreement_view.xml",
        "views/account_journal_view.xml",
        "views/account_move_view.xml",
        "wizard/service_billing_preparation_view.xml",
        "wizard/service_billing_view.xml",
        "wizard/service_distribution_view.xml",
        "wizard/service_price_change_view.xml",
        "wizard/service_change_invoice_date_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "application": False,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
