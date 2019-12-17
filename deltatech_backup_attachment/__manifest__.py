# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Backup Attachments",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    'summary': 'Backup attachments for selected file type',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Administration",
    "depends": ['web', 'base'],
    'data': [
        'wizard/export_attachment_view.xml'
    ],
    "license": "LGPL-3",
    "images": ['static/description/main_screenshot.png'],
    "installable": True,
    'application': False,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
