# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

import html2text

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        if line_id and (add_qty or set_qty):
            order_line = self.env["sale.order.line"].sudo().browse(line_id)
            if order_line.lot_id:
                values = {"line_id": order_line.id, "quantity": 1}
        elif line_id and not (add_qty or set_qty):
            order_line = self.env["sale.order.line"].sudo().browse(line_id)

            discount = order_line.discount
            values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
            # values['discount'] = discount
            order_line = self.env["sale.order.line"].sudo().browse(line_id)
            if order_line and values["quantity"] > 0.0:
                order_line.write({"discount": discount})
            return values
        else:
            return super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

    def _cart_refurbish_update(self, lot_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault("lang", self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env["sale.order.line"].sudo().with_context(product_context)
        # change lang to get correct name of attributes/values

        LotSudo = self.env["stock.production.lot"].sudo().with_context(product_context)
        lot = LotSudo.browse(int(lot_id))
        product_id = lot.product_id.id
        order_line = False
        if self.state != "draft":
            request.session["sale_order_id"] = None
            raise UserError(_("It is forbidden to modify a sales order which is not in draft status."))
        if line_id is not False:
            domain = [("order_id", "=", self.id), ("lot_id", "=", lot.id)]
            order_line = SaleOrderLineSudo.search(domain)

        if not order_line:
            values = self._website_product_id_change(self.id, product_id, qty=1)
            values["lot_id"] = lot.id
            values["discount"] = lot.discount
            # create the line
            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))

        return {"line_id": order_line.id}


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one("stock.production.lot")

    @api.onchange("product_id", "price_unit", "product_uom", "product_uom_qty", "tax_id", "lot_id")
    def _onchange_discount(self):
        super(SaleOrderLine, self)._onchange_discount()
        if self.lot_id:
            self.product_uom_qty = 1
            self.discount = self.lot_id.discount

    # de verificat dispobibilitatea stocului daca este selectat lotul

    #
    def get_description_following_lines(self):
        res = super(SaleOrderLine, self).get_description_following_lines()
        if self.lot_id:
            res = res + [html2text.html2text(self.lot_id.note)]

        return res

    def _compute_name_short(self):
        super(SaleOrderLine, self)._compute_name_short()
        for record in self:
            if record.lot_id:
                record.name_short = _("Refurbish:") + record.name_short

    @api.onchange("lot_id")
    def onchange_lot_id(self):
        if self.lot_id:
            self.product_uom_qty = 1
            self.discount = self.lot_id.discount

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        if self.lot_id:
            values["lot_id"] = self.lot_id.id
        return values

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        if self.lot_id:
            for orderline in self:
                for move in orderline.move_ids:
                    move.move_line_ids.write({"lot_id": orderline.lot_id.id})
