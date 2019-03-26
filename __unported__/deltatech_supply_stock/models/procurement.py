# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, registry, _
from odoo.tools import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def _quantity_in_progress(self):
        return super(Orderpoint, self)._quantity_in_progress()


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    # sa se ruleze aprovizionarea doar pentru produsele specificate
    def _get_orderpoint_domain(self, company_id=False):
        domain = super(ProcurementGroup, self)._get_orderpoint_domain(company_id)
        if 'product_ids' in self.env.context:
            domain += [('product_id', 'in', self.env.context['product_ids'])]
        return domain


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, supplier):
        procurement_uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id._select_seller(
            partner_id=supplier.name,
            quantity=procurement_uom_po_qty,
            date=po.date_order ,
            uom_id=product_id.uom_po_id)

        if procurement_uom_po_qty < supplier.min_qty:
            msg = 'Cantitatea %s este mai mica decat %s impusa de furnizorul %s' % (procurement_uom_po_qty,
                                                                                    supplier.min_qty,
                                                                                    supplier.name.name)
            po.message_post(body=msg)
            product_qty = product_id.uom_po_id._compute_quantity(supplier.min_qty, product_uom)

        res = super(ProcurementRule, self)._prepare_purchase_order_line(product_id, product_qty, product_uom, values,
                                                                        po, supplier)
        return res

#     @api.model
#     def run_scheduler(self, use_new_cursor=False, company_id=False):
#         products = self.env['product.product'].search([('type', '=', 'product')])
#         self.supply(products, use_new_cursor, company_id)
#         return super(ProcurementOrder, self).run_scheduler(use_new_cursor, company_id)
#
#     def supply(self, products, use_new_cursor=False, company_id=False):
#         try:
#             if use_new_cursor:
#                 cr = registry(self._cr.dbname).cursor()
#                 self = self.with_env(self.env(cr=cr))  # TDE FIXME
#
#             if not company_id:
#                 company_id = self.env.user.company_id
#
#             warehouse = company_id.warehouse_id
#
#             location = warehouse.lot_stock_id
#             procurements = self.env["procurement.order"]
#             for product in products:
#                 if product.virtual_available < 0:
#                     qty = -1 * product.virtual_available
#                     # cate aprovizionari sunt in exceptie ?
#                     procurements = self.search([('product_id', '=', product.id),
#                                                 ('state', 'in', ['exception', 'running']),
#                                                 ('location_id', '=', location.id)])
#                     procurements.run()
#                     for procurement in procurements:
#                         # if not procurement.production_id:  # se scade daca nu este facuta o comadna de productie
#                         qty = qty - procurement.product_qty
#
#                     if not float_is_zero(qty, precision_digits=2):
#                         # Cum sa determin care este data la care sunt necesare produsele?
#
#                         msg = _("Today %s the stock quantity is %s and forecast incoming is %s and outgoing is %s") % (
#                             fields.Date.today(), str(product.qty_available),
#                             str(product.incoming_qty), str(product.outgoing_qty)
#                         )
#                         move = self.env['stock.move'].search([('product_id', '=', product.id),
#                                                               ('state', 'in', ['waiting', 'confirmed']),
#                                                               ('location_id', '=', location.id)], limit=1,
#                                                              order='date_expected')
#                         date_planned = move.date_expected or fields.Datetime.now(),
#                         date_planned = max(fields.Datetime.now(), date_planned)
#
#                         procurement = self.create({
#                             'name': 'SUP: %s' % (self.env.user.login),
#                             'date_planned': date_planned,
#                             'product_id': product.id,
#                             'product_qty': qty,
#                             'product_uom': product.uom_id.id,
#                             'warehouse_id': warehouse.id,
#                             'location_id': location.id,
#                             'group_id': move.group_id.id,
#                             'company_id': company_id.id})
#
#                         procurement.message_post(body=msg)
#                         procurements |= procurement
#
#             if procurements and use_new_cursor:
#                 self.env.cr.commit()
#         finally:
#             if use_new_cursor:
#                 try:
#                     self.env.cr.close()
#                 except Exception:
#                     pass
#         return {}
#
#     # sa tina cont de cantitatea minima de aprovizionat
#     @api.multi
#     def _prepare_purchase_order_line(self, po, supplier):
#         values = super(ProcurementOrder, self)._prepare_purchase_order_line(po, supplier)
#         #min_qty = self.product_uom._compute_quantity(supplier.min_qty, self.product_id.uom_po_id)
#         if values['product_qty'] < supplier.min_qty:
#             msg = 'Cantitatea %s este mai mica decat %s impusa de furnizorul %s' % (values['product_qty'],
#                                                                                     supplier.min_qty,
#                                                                                     supplier.name.name)
#             self.message_post(body=msg)
#             values['product_qty'] = supplier.min_qty
#         return values
