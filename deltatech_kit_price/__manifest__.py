# © 2026 Deltatech
# See README.rst file on the addons root folder for license details

{
    "name": "Deltatech Kit Price",
    "summary": "Compute product cost price in sale order line based on kit",
    "version": "19.0.0.0.2",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing/Manufacturing",
    # `mrp_account` furnizează `product.product._compute_bom_price`, folosit în
    # `_compute_purchase_price`. E `auto_install`, deci se instala din întâmplare
    # când era în bază și alt modul care îl cere explicit.
    "depends": ["sale_margin", "mrp", "mrp_account"],
    "license": "OPL-1",
    "data": [],
    "application": False,
    "installable": True,
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
