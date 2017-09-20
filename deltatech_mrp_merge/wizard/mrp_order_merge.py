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

        # product_qty = main_production.product_qty
        # for production in self.production_ids:
        #    if production != main_production:
        #        product_qty += production.product_qty
        # main_production.write({'product_qty': product_qty,
        #                       'bom_id': False,
        #                       'product_id': False})
        # main_production.move_finished_ids.write({'product_uom_qty': product_qty})
        # produsul din antet trebui inlocuit cu unul dummy
        # comanda nu mai trebuie sa aiba lista de materiale


        raw_picking = main_production.move_raw_ids[0].picking_id
        finished_picking = main_production.move_finished_ids[0].picking_id
        raw_value = {'raw_material_production_id': main_production.id}
        if raw_picking:
            raw_value['picking_id'] = raw_picking.id
        finished_value = {'production_id': main_production.id}
        if finished_picking:
            finished_value['picking_id'] = finished_picking.id

        for production in self.production_ids:
            if production != main_production:
                production.move_raw_ids.write(raw_value)
                # trebuie sa anulez miscarea pentru receptia produsului finit ?
                production.move_finished_ids.write(finished_value)
                production.workorder_ids.write({'production_id': main_production.id})
                production.procurement_ids.write({'production_id': main_production.id})
                production.write({'state': 'cancel'})
                production.unlink()

        if raw_picking:
            raw_picking.recheck_availability()

        if finished_picking:
            finished_picking.do_propare_partial()

        main_production.write({'state': 'progress',
                               'check_to_done': False})  # comanda este in progres

        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = "[('id','in', " + str(self.production_ids.ids) + ")]"
        return action
