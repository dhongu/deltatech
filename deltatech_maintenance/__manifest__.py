# ©  2008-2022 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Maintenance Extension",
    "summary": "Maintenance Extension",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Human Resources",
    "depends": ["maintenance", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/maintenance_view.xml",
        "views/stock_picking_view.xml",
        # 'views/res_config_view.xml',
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
