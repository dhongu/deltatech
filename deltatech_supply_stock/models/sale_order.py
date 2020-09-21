# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        route_buy = self.env.ref("purchase.route_warehouse0_buy", raise_if_not_found=False)
        route_manufacture = self.env.ref("mrp.route_warehouse0_manufacture", raise_if_not_found=False)
        for order in self:
            for line in order.order_line:
                if route_manufacture and route_manufacture.id in line.product_id.route_ids.ids:
                    bom = self.env["mrp.bom"].search(
                        [
                            "|",
                            ("product_id", "=", line.product_id.id),
                            ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                        ]
                    )
                    if not bom:
                        raise UserError(_("Product %s without BOM") % line.product_id.name)
                else:
                    if route_buy and route_buy.id in line.product_id.route_ids.ids:
                        if not line.product_id.seller_ids:
                            raise UserError(_("Product %s without vendor") % line.product_id.name)

        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # se suprascrie metoda standard pentru a nu mai generea eroare
    def _check_routing(self):
        if self.product_id.route_ids:  # de aprovizioneaza de undeva
            is_available = True
        else:
            is_available = super(SaleOrderLine, self)._check_routing()
        return is_available
