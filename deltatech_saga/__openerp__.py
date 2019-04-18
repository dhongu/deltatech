# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
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
    "name": "Deltatech SAGA Interface",
    "version": "2.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Permite exportul de date din Odoo pentru a fi importate in Saga
 - Permite importul de clienti si furnizori din SAGA
 - Partenerii au doua referinte pentru codurile de client respectiv de furnizor din SAGA
 - categoriile de porduse au un camp nou pentru tipul de acticol din SAGA  


Nota:
La export se preiua ultimile 4 caractere din nr de factura la care se adauga 10000 si se formeaza nr de NIR.

    """,

    "category": "Generic Modules/Base",
    "depends": ['deltatech', "base", "account", "l10n_ro_invoice_report"],
    "external_depends": ['dbf'],
    "price": 150.00,
    "currency": "EUR",

    "license": "AGPL-3",
    "data": [
        'data/data.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'wizard/export_saga_view.xml',
        'wizard/import_saga_view.xml',
    ],

    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
