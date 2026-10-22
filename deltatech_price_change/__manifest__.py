# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Price Change",
    "summary": "Track list price changes, price change report and document",
    "version": "19.0.1.2.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules",
    "depends": ["base", "stock", "product", "sale"],
    "license": "OPL-1",
    "data": [
        "views/product_view.xml",
        "views/product_price_change_view.xml",
        "views/product_price_change_log_view.xml",
        "views/price_change_report.xml",
        "views/report_pricechange.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
