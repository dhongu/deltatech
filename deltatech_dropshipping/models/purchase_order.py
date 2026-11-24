# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools import format_amount


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_price_warning = fields.Html(compute="_compute_purchase_price_warning")

    @api.depends(
        "company_id",
        "currency_id",
        "date_order",
        "order_line.price_unit",
        "order_line.discount",
        "order_line.tax_ids",
        "order_line.product_uom_id",
        "order_line.sale_line_id.price_unit",
        "order_line.sale_line_id.discount",
        "order_line.sale_line_id.tax_ids",
        "order_line.sale_line_id.product_uom_id",
        "order_line.sale_line_id.order_id.currency_id",
        "order_line.sale_line_id.order_id.date_order",
    )
    def _compute_purchase_price_warning(self):
        for order in self:
            company = order.company_id or self.env.company
            company_currency = company.currency_id
            warnings = []
            for line in order.order_line.filtered("sale_line_id"):
                sale_line = line.sale_line_id
                # Prețul de achiziție net (discount, fără taxe), pe UM de bază, în moneda companiei
                purchase_price = self._get_normalized_unit_price(line, order.partner_id, order.date_order, company)
                # Prețul de vânzare net (discount, fără taxe), pe UM de bază, în moneda companiei
                sale_price = self._get_normalized_unit_price(
                    sale_line, sale_line.order_id.partner_id, sale_line.order_id.date_order, company
                )

                if company_currency.compare_amounts(purchase_price, sale_price) > 0:
                    warnings.append(
                        self.env._(
                            "<li><strong>%(product)s</strong>: Purchase %(purchase)s > Sale %(sale)s (Diff: %(diff)s)</li>",
                            product=line.product_id.display_name,
                            purchase=format_amount(self.env, purchase_price, company_currency),
                            sale=format_amount(self.env, sale_price, company_currency),
                            diff=format_amount(self.env, purchase_price - sale_price, company_currency),
                        )
                    )
            if warnings:
                order.purchase_price_warning = "<ul>" + "".join(warnings) + "</ul>"
            else:
                order.purchase_price_warning = False

    @api.model
    def _get_normalized_unit_price(self, line, partner, date, company):
        """Prețul unitar al unei linii (purchase.order.line sau sale.order.line) adus la o bază comună:
        - după discountul liniei,
        - fără taxe,
        - pe unitatea de măsură de bază a produsului,
        - în moneda companiei, la cursul de la data comenzii.
        """
        currency = line.order_id.currency_id or company.currency_id
        price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
        taxes = line.tax_ids.compute_all(price, currency, 1.0, product=line.product_id, partner=partner)
        price = taxes["total_excluded"]

        product_uom = line.product_id.uom_id
        if line.product_uom_id and product_uom and line.product_uom_id != product_uom:
            price = line.product_uom_id._compute_price(price, product_uom)

        if currency != company.currency_id:
            price = currency._convert(
                price,
                company.currency_id,
                company,
                fields.Date.to_date(date) or fields.Date.context_today(self),
                round=False,
            )
        return price
