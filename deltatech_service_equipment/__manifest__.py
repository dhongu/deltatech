# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Services Equipment",
    "summary": "service equipment management",
    "version": "13.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services",
    "depends": ["deltatech_service", "analytic", "maintenance"],
    "license": "AGPL-3",
    "data": [
        "data/data.xml",
        #
        "views/service_agreement_view.xml",
        #
        # 'service_efficiency_report.xml',
        # 'stock_view.xml',
        "security/service_security.xml",
        "security/ir.model.access.csv",
        #
        # 'wizard/estimate_view.xml',
        "wizard/enter_readings_view.xml",
        # 'wizard/service_equi_operation_view.xml',
        "wizard/service_equi_agreement_view.xml",
        #
        "views/service_meter_view.xml",
        "views/service_equipment_view.xml",
        # 'service_consumable_view.xml',
        #
        # 'demo.xml',
        # # 'service.meter.reading.csv'
    ],
    "images": ["images/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
