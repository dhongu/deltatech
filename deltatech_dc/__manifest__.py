# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Declaration of Conformity",
    "summary": "Print Declaration of Conformity",
    "version": "19.0.1.0.12",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Generic Modules/Other",
    "depends": [
        "base",
        "product",
        "sale",
        "mrp",
        "product_expiry",
        # `account.move._get_invoiced_lot_values()`, apelat în report/report_dc.py,
        # e definit în `stock_account` (extins apoi de `sale_stock`).
        "stock_account",
        # "stock_picking_invoice_link"
    ],
    "data": [
        "views/product_view.xml",
        "views/production_lot_view.xml",
        "views/deltatech_dc_view.xml",
        "views/deltatech_dc_report.xml",
        "views/report_dc_second_form.xml",
        "views/report_dc.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/data.xml",
        "views/warranty_certificate.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
