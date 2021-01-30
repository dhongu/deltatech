# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from openerp import models, fields, api, _


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    ral_id = fields.Many2one('product.product', 'RAL', states={'draft': [('readonly', False)]}, readonly=True,
                             domain=[('default_code', 'like', 'RAL%')])

    @api.multi
    def action_confirm(self):

        picking_id = super(mrp_production, self).action_confirm()

        for production in self:
            if production.ral_id and production.product_id.track_production:
                for move in production.move_created_ids:
                    if not move.restrict_lot_id:
                        prodlot_id = self.env['stock.production.lot'].create({
                            'product_id': production.product_id.id,
                            'prefix': production.ral_id.default_code,
                            'ral_id': production.ral_id.id,
                            'date': production.date_planned
                        })
                        move.write({'restrict_lot_id': prodlot_id})
                    elif not move.restrict_lot_id.ral_id:
                        move.prodlot_id.write({
                            'prefix': production.ral_id.default_code,
                            'ral_id': production.ral_id.id
                        })

        return picking_id

    @api.multi
    def action_compute(self, properties=[]):
        """ Computes bills of material of a product.
        @param properties: List containing dictionaries of properties.
        @return: No. of products.
        """
        result = super(mrp_production, self).action_compute(properties)
        for production in self:
            if production.ral_id and (production.product_id.track_production or production.product_id.track_all):
                for line in production.product_lines:
                    if line.product_id.default_code == 'RAL 0000':
                        line.write({
                            'product_id': production.ral_id.id,
                            'name': production.ral_id.name
                        })

        return result


class mrp_product_produce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.model
    def _get_lot_id(self):
        """ To obtain lot_id 
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: id lot
        """

        production = self.pool.get('mrp.production').browse(self.env.context['active_id'])

        prodlot_id = None
        if production.ral_id and (production.product_id.track_production or production.product_id.track_all):
            for move in production.move_created_ids:
                if not move.restrict_lot_id:
                    prodlot_id = self.env['stock.production.lot'].create({
                        'product_id': production.product_id.id,
                        'prefix': production.ral_id.default_code,
                        'ral_id': production.ral_id.id,
                        'date': production.date_planned
                    })

                else:
                    prodlot_id = move.restrict_lot_id

        return prodlot_id

    _defaults = {
        'lot_id': _get_lot_id,
    }
