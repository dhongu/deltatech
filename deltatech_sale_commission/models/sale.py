# ©  2017-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    commission = fields.Float(string="Commission", default=0.0)

    @api.depends("product_id", "company_id", "currency_id", "product_uom")
    def _compute_purchase_price(self):
        # product_id = self.env["ir.config_parameter"].sudo().get_param("sale.default_deposit_product_id")
        company = self.company_id or self.env.user.company_id
        deposit_product = company.sale_down_payment_product_id
        res = super()._compute_purchase_price()
        for line in self:
            if line.product_id.id == deposit_product.id:
                line.purchase_price = line.price_unit
        return res
