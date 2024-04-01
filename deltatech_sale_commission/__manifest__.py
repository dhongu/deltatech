# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Commission",
    "summary": "Compute sale commission",
    "version": "17.0.1.1.8",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["deltatech_sale_margin"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/account_invoice_view.xml",
        "report/sale_margin_report.xml",
        "views/commission_users_view.xml",
        "wizard/commission_compute_view.xml",
        "wizard/update_purchase_price_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
