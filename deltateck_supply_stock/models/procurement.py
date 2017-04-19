# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id=False):

        warehouse = self.env['stock.warehouse'].search([], limit=1)
        location = warehouse.lot_stock_id
        products = self.env['product.product'].search([('type', '=', 'product')])

        for product in products:
            if product.virtual_available < 0:
                qty = -1 * product.virtual_available
                # cite aprovizionari sunt in exceptie ?
                procurements = self.search([('product_id', '=', product.id),
                                            ('state', 'in', ['exception', 'running']),
                                            ('location_id', '=', location.id)])
                procurements.run()
                for procurement in procurements:
                    qty = qty - procurement.product_qty
                if qty > 0:
                    # mum sa determin care este data la care sunt necesare produsele?

                    msg = _("Today %s the stock quantity is %s and forecast incoming is %s and outgoing is %s") % (
                        fields.Date.today(), str(product.qty_available),
                        str(product.incoming_qty), str(product.outgoing_qty)
                    )
                    move = self.env['stock.move'].search(
                                        [('product_id', '=', product.id),
                                         ('state', 'in', ['waiting', 'confirmed']),
                                         ('location_id', '=', location.id)], limit=1, order='date_expected')
                    date_planned = move.date_expected or fields.Datetime.now(),
                    date_planned = max(fields.Datetime.now(), date_planned )
                    procurement = self.create({
                        'name': 'SUP: %s' % (self.env.user.login),
                        'date_planned': date_planned,
                        'product_id': product.id,
                        'product_qty': qty,
                        'product_uom': product.uom_id.id,
                        'warehouse_id': warehouse.id,
                        'location_id': location.id,
                        'company_id': warehouse.company_id.id})

                    procurement.message_post(body=msg)

        return super(ProcurementOrder, self).run_scheduler(use_new_cursor, company_id)
