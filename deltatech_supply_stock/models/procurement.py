# -*- coding: utf-8 -*-


from odoo import api, fields, models, registry, _
from odoo.tools import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id=False):
        products = self.env['product.product'].search([('type', '=', 'product')])
        self.supply(products, use_new_cursor, company_id)
        return super(ProcurementOrder, self).run_scheduler(use_new_cursor, company_id)

    def supply(self, products, use_new_cursor=False, company_id=False):
        try:
            if use_new_cursor:
                cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))  # TDE FIXME

            warehouse = self.env['stock.warehouse'].search([], limit=1)
            location = warehouse.lot_stock_id
            procurements = self.env["procurement.order"]
            for product in products:
                if product.virtual_available < 0:
                    qty = -1 * product.virtual_available
                    # cate aprovizionari sunt in exceptie ?
                    procurements = self.search([('product_id', '=', product.id),
                                                ('state', 'in', ['exception', 'running']),
                                                ('location_id', '=', location.id)])
                    procurements.run()
                    for procurement in procurements:
                        # if not procurement.production_id:  # se scade daca nu este facuta o comadna de productie
                        qty = qty - procurement.product_qty

                    if not float_is_zero(qty, precision_digits=2):
                        # Cum sa determin care este data la care sunt necesare produsele?

                        msg = _("Today %s the stock quantity is %s and forecast incoming is %s and outgoing is %s") % (
                            fields.Date.today(), str(product.qty_available),
                            str(product.incoming_qty), str(product.outgoing_qty)
                        )
                        move = self.env['stock.move'].search([('product_id', '=', product.id),
                                                              ('state', 'in', ['waiting', 'confirmed']),
                                                              ('location_id', '=', location.id)], limit=1,
                                                             order='date_expected')
                        date_planned = move.date_expected or fields.Datetime.now(),
                        date_planned = max(fields.Datetime.now(), date_planned)

                        procurement = self.create({
                            'name': 'SUP: %s' % (self.env.user.login),
                            'date_planned': date_planned,
                            'product_id': product.id,
                            'product_qty': qty,
                            'product_uom': product.uom_id.id,
                            'warehouse_id': warehouse.id,
                            'location_id': location.id,
                            'group_id': move.group_id.id,
                            'company_id': warehouse.company_id.id})

                        procurement.message_post(body=msg)
                        procurements |= procurement

            if procurements and use_new_cursor:
                self.env.cr.commit()
        finally:
            if use_new_cursor:
                try:
                    self.env.cr.close()
                except Exception:
                    pass
        return {}

    # sa tina cont de cantitatea minima de aprovizionat
    @api.multi
    def _prepare_purchase_order_line(self, po, supplier):
        values = super(ProcurementOrder, self)._prepare_purchase_order_line(po, supplier)
        #min_qty = self.product_uom._compute_quantity(supplier.min_qty, self.product_id.uom_po_id)
        if values['product_qty'] < supplier.min_qty:
            msg = 'Cantitatea %s este mai mica decat %s impusa de furnizorul %s' % (values['product_qty'],
                                                                                    supplier.min_qty,
                                                                                    supplier.name.name)
            self.message_post(body=msg)
            values['product_qty'] = supplier.min_qty
        return values
