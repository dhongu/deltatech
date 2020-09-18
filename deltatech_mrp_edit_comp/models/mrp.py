# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # def action_assign(self):
    #
    #     for production in self:
    #         dummy_id = 1 # self.env.ref('mrp.mrp_dummy_bom_line').id or 1
    #
    #         new_move = production.move_raw_ids.filtered(lambda x: x.state == 'draft')
    #         for move in new_move:
    #             move.write({'location_dest_id': move.product_id.property_stock_production.id,
    #                         'unit_factor': 1.0,
    #                         'bom_line_id': dummy_id,
    #                         'state': 'confirmed'})
    #         new_move.action_assign()
    #     super(mrp_production, self).action_assign()
    #     return True

    """
    @api.onchange('move_raw_ids')
    def onchange_move_raw_product_id(self):
        for raw in self.move_raw_ids:
            raw.location_dest_id = raw.product_id.property_stock_production
            if raw.state == 'draft':
                raw.state = 'confirmed'
            if not raw.unit_factor:
                raw.unit_factor = 1.0
    """
