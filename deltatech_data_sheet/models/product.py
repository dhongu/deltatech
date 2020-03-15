# -*- coding: utf-8 -*-
# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, _



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # {'default_public':True,'default_res_model':'ir.ui.view'}
    data_sheet_id = fields.Many2one('ir.attachment', string='Data Sheet',
                                    domain=[('mimetype','=','application/pdf'),('public','=',True)])

    safety_data_sheet_id = fields.Many2one('ir.attachment', string='Safety Data Sheet',
                                    domain=[('mimetype','=','application/pdf'),('public','=',True)])