# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Services Equipment",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:

- gestionare echipamente
- gestionare contoare  
- gestionare citiri contoare
- facturare in baza citirilor
- caclul estimare citiri
- intoducere automat la sfarsit de perioada a valorilor estimate

    """,

    "category": "Generic Modules",
    "depends": [
        "deltatech_service",
    ],

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
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
