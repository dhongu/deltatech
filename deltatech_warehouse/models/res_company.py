# -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models, fields



class res_company(models.Model):
    _inherit = 'res.company'


    warehouse_id = fields.Many2one('stock.warehouse', string="Default Warehouse")