# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Services Equipment",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Services",
    "depends": [
        "deltatech_service",
    ],

    "license": "AGPL-3",
    "data": [
         'data/data.xml',
        #
        'views/service_rent_view.xml',
        #
        # 'service_efficiency_report.xml',
        # 'stock_view.xml',
         'security/service_security.xml',
         'security/ir.model.access.csv',
        #
        # 'wizard/estimate_view.xml',
        # 'wizard/enter_readings_view.xml',
        # 'wizard/service_equi_operation_view.xml',
        'wizard/service_equi_agreement_view.xml',
        #
        'views/service_meter_view.xml',
        'views/service_equipment_view.xml',
        # 'service_consumable_view.xml',
        #
        # 'demo.xml',
        # # 'service.meter.reading.csv'

    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
