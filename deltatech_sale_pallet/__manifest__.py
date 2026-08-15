# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Pallet",
    "summary": "Sale pallet",
    "version": "19.0.1.0.9",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    # `stock` e folosit de teste (`stock.quant._update_available_quantity`).
    "depends": ["sale_margin", "account", "stock"],
    "license": "OPL-1",
    "data": ["views/product_view.xml", "views/invoice_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
