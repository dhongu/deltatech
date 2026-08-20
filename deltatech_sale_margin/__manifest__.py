# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Margin",
    "summary": "Check price in sale order",
    "version": "19.0.1.2.0",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    # sale_stock_margin keeps `purchase_price` in line with the actual
    # valuation of the delivery, which is the cost the margin check has to
    # use; it is auto_install, but the dependency is declared so the
    # behaviour does not depend on install order
    "depends": ["sale_margin", "sale_stock_margin", "account", "stock_account", "delivery"],
    "license": "OPL-1",
    "data": [
        "security/sale_security.xml",
        "views/sale_margin_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
