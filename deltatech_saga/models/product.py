# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import math

 

class product_category(models.Model):
    _inherit = "product.category" 

    code_saga = fields.Char(string="Code SAGA", size=2)
    saga_standard_code = fields.Selection([
        ('01','Marfuri 371'),
        ('02','Materii prime 301'),
        ('03','Materiale auxiliare 3021'),
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

