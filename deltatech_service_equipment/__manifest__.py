# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Services Equipment",
    "summary": "Service Equipment Management",
    "version": "14.0.1.0.5",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Equipment",
    "depends": ["deltatech_service", "analytic", "maintenance", "stock", "deltatech_download"],
    "external_dependencies": {"python": ["xlwt"]},
    "license": "AGPL-3",
    "data": [
        "data/data.xml",
        "views/service_agreement_view.xml",
        # 'service_efficiency_report.xml',
        # 'stock_view.xml',
        "security/service_security.xml",
        "security/ir.model.access.csv",
        # 'wizard/estimate_view.xml',
        "wizard/enter_readings_view.xml",
        "wizard/service_equi_operation_view.xml",
        # "wizard/service_equi_agreement_view.xml",
        "views/service_meter_view.xml",
        "views/service_equipment_view.xml",
        "views/service_history_view.xml",
        "views/stock_location_view.xml",
        "views/res_config_view.xml",
        "views/account_move_view.xml",
        "views/product_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
