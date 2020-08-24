# -*- coding: utf-8 -*-
# ©  2008-2020  Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    property_maintenance_picking_type = fields.Many2one('stock.picking.type',
                                                        readonly=False,
                                                        string='Stock Operation Type for Maintenance')
