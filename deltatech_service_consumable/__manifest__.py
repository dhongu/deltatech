# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Services Consumable",
    "summary": "Service Consumable",
    "version": "14.0.1.0.6",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Equipment",
    "depends": [
        "deltatech_service",
        "deltatech_service_equipment",
        "deltatech_product_extension",
        "deltatech_stock_report",
    ],
    "license": "AGPL-3",
    "data": [
        # 'service_consumable_view.xml',
        "views/service_equipment_view.xml",
        "views/stock_picking_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
