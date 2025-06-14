# ©  2024 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech OBYC - Account Determination",
    "version": "17.0.1.0.0",
    "summary": "Implementare OBYC-style account mapping pentru tranzacții de stoc",
    "category": "Accounting",

    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "data": [
        "security/ir.model.access.csv",
        "views/product_account_determination_views.xml",
        "views/account_modifier_views.xml",
        "views/product_valuation_class_views.xml",
        "views/product_valuation_area_views.xml",
        "views/menu_views.xml",
    ],
     "depends": ["stock", "account"],
    "license": "LGPL-3",
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}



