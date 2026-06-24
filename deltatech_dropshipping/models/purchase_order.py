# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_price_warning = fields.Html(compute="_compute_purchase_price_warning")

    @api.depends(
        "order_line.price_unit",
        "order_line.tax_ids",
        "order_line.sale_line_id.price_unit",
        "order_line.sale_line_id.tax_ids",
    )
    def _compute_purchase_price_warning(self):
        for order in self:
            warnings = []
            for line in order.order_line:
                if line.sale_line_id:
                    # Prețul de achiziție din PO fără taxe
                    taxes_p = line.tax_ids.compute_all(
                        line.price_unit,
                        line.order_id.currency_id,
                        1.0,
                        product=line.product_id,
                        partner=order.partner_id,
                    )
                    purchase_price = taxes_p["total_excluded"]

                    # Prețul de vânzare din SO fără taxe
                    taxes_s = line.sale_line_id.tax_ids.compute_all(
                        line.sale_line_id.price_unit,
                        line.sale_line_id.order_id.currency_id,
                        1.0,
                        product=line.sale_line_id.product_id,
                        partner=line.sale_line_id.order_id.partner_id,
                    )
                    sale_price = taxes_s["total_excluded"]

                    if purchase_price > sale_price:
                        diff = round(purchase_price - sale_price, 2)
                        warnings.append(
                            self.env._(
                                "<li><strong>%(product)s</strong>: Purchase %(purchase)s > Sale %(sale)s (Diff: %(diff)s)</li>",
                                product=line.product_id.display_name,
                                purchase=round(purchase_price, 2),
                                sale=round(sale_price, 2),
                                diff=diff,
                            )
                        )
            if warnings:
                order.purchase_price_warning = "<ul>" + "".join(warnings) + "</ul>"
            else:
                order.purchase_price_warning = False
