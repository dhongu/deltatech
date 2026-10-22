# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Commission",
    "summary": "Salesperson commissions on the profit report of the invoices",
    "version": "19.0.2.0.0",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["deltatech_sale_margin"],
    "license": "OPL-1",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "report/sale_margin_report.xml",
        "views/commission_users_view.xml",
        "wizard/commission_compute_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
