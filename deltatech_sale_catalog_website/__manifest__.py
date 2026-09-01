# ©  2024 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "Sale Catalog Website Categories & Image Zoom",
    "summary": "In the Sales product catalog: show website categories in the "
    "left panel and open the product image full size on click",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Sales",
    "depends": ["sale", "website_sale"],
    "data": [
        "views/product_catalog_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "deltatech_sale_catalog_website/static/src/product_catalog/search_model.esm.js",
            "deltatech_sale_catalog_website/static/src/product_catalog/catalog_view.esm.js",
            "deltatech_sale_catalog_website/static/src/product_catalog/image_zoom_field.esm.js",
            "deltatech_sale_catalog_website/static/src/product_catalog/image_zoom_field.xml",
            "deltatech_sale_catalog_website/static/src/product_catalog/image_zoom_field.scss",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
