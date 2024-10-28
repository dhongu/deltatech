##############################################################################

{
    "name": "Product Labels",
    "version": "18.0.1.0.6",
    "category": "Stock",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "AGPL-3",
    "summary": "Print Labels on Products",
    "depends": ["product", "sale"],
    "data": [
        "views/report_product_labels.xml",
        "views/terrabit_product_label_print_view.xml",
        "security/ir.model.access.csv",
        # "views/product_view.xml",
    ],
    "development_status": "Mature",
}
