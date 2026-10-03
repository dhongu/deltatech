# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Simple MRP barcode",
    "summary": "Simple production",
    "version": "20.0.0.0.2",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing",
    "depends": ["deltatech_mrp_simple", "barcodes"],
    "license": "OPL-1",
    "data": [
        "views/mrp_simple_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "deltatech_mrp_simple_barcode/static/src/js/barcode_handler_field.esm.js",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["VoicuStefan2001"],
}
