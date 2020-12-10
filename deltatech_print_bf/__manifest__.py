# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Print Invoice to ECR",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Generare fisier pentu casa de marcat",
    "category": "Generic Modules",
    "depends": [
        "account",
        "web",
        "sale",
        "deltatech_download",
        "deltatech_partner_generic",
        "deltatech_select_journal",
    ],
    "license": "LGPL-3",
    "data": [
        "wizard/account_invoice_export_bf_view.xml",
        "views/res_config_settings_views.xml",
        "views/pf_sale_views.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
