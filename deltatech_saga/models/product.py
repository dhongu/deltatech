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
#
##############################################################################


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import math


class product_category(models.Model):
    _inherit = "product.category"

    code_saga = fields.Char(string="Code SAGA", size=2)
    saga_standard_code = fields.Selection([
        ('01', 'Marfuri 371'),
        ('02', 'Materii prime 301'),
        ('03', 'Materiale auxiliare 3021'),
        ('14', 'Combustibili 3022'),
        ('15', 'Piese de schimb 3024'),
        ('16', 'Alte mat. consumabile 3028'),
        ('04', 'Produse finite 345'),
        ('05', 'Ambalaje 381'),
        ('06', 'Obiecte de inventar 303'),
        ('07', 'Produse reziduale 346'),
        ('08', 'Semifabricate 341'),
        ('09', 'Amenajari provizorii 323'),
        ('10', 'Mat. spre prelucrare 8032'),
        ('11', 'Mat. în pastrare/consig. 8033'),
        ('12', 'Discount financiar intrari 767'),
        ('13', 'Discount financiar iesiri 667'),
        ('18', 'Discount comercial intrari 609'),
        ('19', 'Discount comercial iesiri 709'),
        ('17', 'Servicii vandute 704'),

    ])

    @api.onchange('saga_standard_code')
    def onchange_saga_standard_code(self):
        self.code_saga = self.saga_standard_code

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
