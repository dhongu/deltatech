# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Sale Order Stage Route",
    "version": "18.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "summary": "Sale Order Stage Route",
    "category": "Sales",
    "depends": ["deltatech_sale_stage", "stock_barcode"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/sale_phase_view.xml",
        "views/sale_view.xml",
        "views/stock_picking_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "deltatech_sale_stage_route/static/src/xml/stock_barcode_templates.xml",
        ],
    },
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
