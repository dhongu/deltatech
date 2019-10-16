# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class PickingType(models.Model):
    _inherit = "stock.picking.type"


    def get_action_stock_simple_transfer(self):
        action = self._get_action('deltatech_stock_transfer.action_stock_simple_transfer')
        action['context'] = {
                    'search_default_picking_type_id': self.id,
                    'default_picking_type_id': self.id,
                    'contact_display': 'partner_address',
                    'search_default_available': 1,
            }
        return action


