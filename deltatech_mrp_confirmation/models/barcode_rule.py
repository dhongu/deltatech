# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields
from odoo.tools.translate import _


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    type = fields.Selection(selection_add=[
            ('mrp_order', _('Production Order')),
            ('mrp_operation', _('Production Operation')),
            ('mrp_worker', _('Worker')),
        ])
