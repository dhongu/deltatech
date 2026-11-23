# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Mail Signature Templates",
    "summary": "One e-mail signature template per company, with fields, generated for every user",
    "version": "19.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "support@terrabit.ro",
    "category": "Productivity/Discuss",
    "depends": ["mail", "html_editor"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/mail_signature_template_views.xml",
        "views/res_users_views.xml",
    ],
    "demo": ["data/mail_signature_template_demo.xml"],
    "images": ["static/description/main_screenshot.png"],
    "price": 5.00,
    "full_price": 5.00,
    "currency": "EUR",
    "development_status": "Beta",
    "consultant_sheet": "full",
    "maintainers": ["dhongu"],
    "installable": True,
    "application": False,
}
