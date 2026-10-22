##############################################################################

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Product Labels",
    "version": "20.0.1.2.0",
    "category": "Stock",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "summary": "Print product and lot labels from products, sale orders and transfers",
    "depends": ["product", "sale", "stock"],
    "data": [
        "views/report_product_labels.xml",
        "views/terrabit_product_label_print_view.xml",
        "security/ir.access.csv",
        # "views/product_view.xml",
    ],
    "development_status": "Mature",
}
