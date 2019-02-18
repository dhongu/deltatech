# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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
    "name": "Deltatech Sale RFQ",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Gestioneaza cererile si stadiile de intocmire a unei oferte
 - Din oportunitate se pote genera un RFQ
 - Devizierul din RFQ poate genera o Cotatie noua sau poate anexa o cotatie existenta
 - Din Cotatie se poate seta statusul de cotatie pregatita (status pe RFQ)
 - Dupa ce cotatia este preluata, prelucrata si trimisa la Client se seteaza de Solicitant stare Cotatie Trimisa
 - daca cotatia nu este acceptata de client Solicitantul poate sa seteze starea de Ajustare Cotatie
  
  
Nu se va folosi modulul sale_crm
  
    """,

    'category': 'Sales Management',
    "depends": ['deltatech',
                "sale", "crm"
                ],

    "license": "AGPL-3", "data": [
        "security/security.xml", "security/ir.model.access.csv",
        "sale_rfq_view.xml",
        "data.xml",
        "sale_view.xml",
        "crm_lead_view.xml"
    ],

    "active": False,
    "installable": True,
}
