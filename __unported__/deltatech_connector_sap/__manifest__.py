# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Connector SAP",
    "version": "1.0",
    "author": "Deltatech",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Administration",
    'external_dependencies': {
        'python': [
            'pyrfc',
        ],
    },
    "depends": ["base", "stock", "product"],
    'data': [
        'connector_sap_view.xml'
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
