# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Services Agreement",
    "summary": "Manage Services Agreement",
    "version": "13.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Service Management",
    "depends": ["base", "product", "account", "date_range"],
    "license": "AGPL-3",
    "data": [
        "data/data.xml",
        "security/service_security.xml",
        "security/ir.model.access.csv",
        "views/service_consumption_view.xml",
        "views/service_agreement_view.xml",
        "wizard/service_billing_preparation_view.xml",
        "wizard/service_billing_view.xml",
        "wizard/service_distribution_view.xml",
        "wizard/service_price_change_view.xml",
        "wizard/service_change_invoice_date_view.xml",
        # "views/account_invoice_penalty_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "application": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
