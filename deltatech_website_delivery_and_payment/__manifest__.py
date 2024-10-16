# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Delivery and Payment",
    "category": "Website",
    "summary": "eCommerce Delivery and Payment constrains",
    "version": "17.0.2.1.4",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale_stock"],
    "data": [
        "views/delivery_view.xml",
        "views/templates.xml",
        "views/payment_view.xml",
        "views/res_partner_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_frontend": ["deltatech_website_delivery_and_payment/static/src/js/payment_form.esm.js"],
    },
}
