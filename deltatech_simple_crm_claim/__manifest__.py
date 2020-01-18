# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Simple Claims Management',
    'version': '1.0',
    'category': 'Customer Relationship Management',

    'author': 'OpenERP SA, Terrabit',
    'website': 'https://www.odoo.com',
    'depends': ['sales_team'],
    'data': [
        'views/crm_claim_view.xml',
        'views/crm_claim_menu.xml',
        'security/ir.model.access.csv',
        'report/crm_claim_report_view.xml',
        'data/crm_claim_data.xml',
        'views/res_partner_view.xml',
    ],
    "images": ['images/main_screenshot.png'],
    #'demo': ['data/crm_claim_demo.xml'],
    'test': [
        'test/process/claim.yml',
        'test/ui/claim_demo.yml'
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
