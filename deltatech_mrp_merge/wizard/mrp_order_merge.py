# coding=utf-8


from odoo import models, fields, api


class MrpOrderMerge(models.TransientModel):
    _name = 'mrp.order.merge'
    _description = "MRP Production Order Merge"

    production_ids = fields.Many2many('mrp.production', string='Production Order')

    @api.model
    def default_get(self, fields):
        defaults = super(MrpOrderMerge, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)

        domain = [('id', 'in', active_ids), ('state', 'in', ['confirmed'])]
        res = self.env['mrp.production'].search(domain)
        defaults['production_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.multi
    def do_merge(self):
        if not self.production_ids:
            return
        main_production = self.production_ids[0]
        # prima comanda din lista devine comanda principala
        product_qty = main_production.product_qty
        for production in self.production_ids:
            if production != main_production:
                product_qty += production.product_qty
        main_production.write({'product_qty': product_qty})
        main_production.move_finished_ids.write({'product_uom_qty': product_qty})

        for production in self.production_ids:
            if production != main_production:
                production.move_raw_ids.write({'raw_material_production_id': main_production.id})
                production.move_finished_ids.write({'production_id': main_production.id, 'state': 'cancel'})
                production.workorder_ids.write({'production_id': main_production.id})
                production.procurement_ids.write({'production_id': main_production.id})
                production.write({'state': 'cancel'})
                production.unlink()

        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = "[('id','in', " + str(
            self.production_ids.ids) + ")]"  # [" + ','.join(map(str, self.production_ids.ids)) + "])]"
        return action
