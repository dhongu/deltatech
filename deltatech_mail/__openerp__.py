# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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
    "name" : "Deltatech Mail Extension",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """

Functionalitati:
 - Trimite email documente din sistem
    - parternerii sunt automat adaugati la urmaritori in documentele trimise
 - Setare documente ca citite
 - Setare documente ca necitite 
     - Nota: pentru a seta simultan mai multe documente trebuie modificata metoda message_mark_as_unread din mail_thread:
             (SELECT id from mail_message where res_id=any(%s) and model=%s limit 1)
             (SELECT id from mail_message where res_id=any(%s) and model=%s)
 - Notificare la primire mesaj
 
 
    """,
    "category" : "Generic Modules/Other",
    "depends" : ['deltatech',"base","mail","web_notification"],
 
    "data" : ['mail_send_to_view.xml',
              'views/deltatech_mail_assets.xml'],
    "active": False,
    "installable": True,
}


