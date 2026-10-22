# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Margin & Profit",
    "summary": "Check price in sale order, cost price on invoices and profit report",
    "version": "19.0.1.3.2",
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
        "security/ir.model.access.csv",
        "security/sale_margin_report_security.xml",
        "views/sale_margin_view.xml",
        "views/res_config_settings_views.xml",
        "views/account_invoice_view.xml",
        "report/sale_margin_report.xml",
        "wizard/update_purchase_price_view.xml",
        "data/cron_jobs.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
