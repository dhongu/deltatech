# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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
    "name": "Deltatech Mail Filter",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - tote emailurile din sistem se trimit la adresa setata prin parametrul mail.always.only.to

 - sistemul totusi trebuie sa permita trimiterea de emailui in situatia in care in context se trimite ignore_always_only_to
    - pentru a se trmite comenzile de vanzare trebuie instalat modul deltatech_mail_filter_sale
    - pentru a se trmite facturile trebuie instalat modulul deltatech_mail_filter_invoice



    """,
    'category': 'Discuss',
    "depends": ['base', 'mail'],

    "data": [],
    "active": False,
    "installable": True,
}
