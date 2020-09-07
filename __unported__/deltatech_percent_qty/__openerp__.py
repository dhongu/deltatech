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
#
##############################################################################

{
    "name": "Deltatech Percent Quantity",
    "version": "2.0",
    "author": "Dorin Hongu",
    "website": "",
    "description": """
    
Functionalitati:
 - Unitate de masura %
 - Camp nou in produs in care se poate specifica un domeniu 
 - daca in comanda de vanzare se utilizeaza un produs care are unitatea de masura procent atunci 
    - pretul este calculat prin suma valorilor liniilor din comanda filtrate cu ajutorul domeniului definit la produs


actualizarea se face manual prin apasarea butonului
<button name="button_update" string="Update Order Line" type="object"   states="draft,sent" groups="base.group_user" />


    """,

    "category": "Generic Modules/Production",
    "depends": ['deltatech', "product", "sale"],


    "data": [
        'product_view.xml',
        'sale_view.xml',
        'data.xml',
    ],


    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
