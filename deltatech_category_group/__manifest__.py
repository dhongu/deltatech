# ©  2008-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Category Group",
    "summary": "Groups for internal categories",
    "version": "14.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Other",
    "depends": [
        "deltatech_sale_commission",
    ],
    "license": "AGPL-3",
    "data": [
        "security/security.xml",
        "views/product_category.xml",
        "views/category_types_views.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
