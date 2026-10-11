# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    mrp_simple_id = fields.Many2one("mrp.simple", string="Simple Production", index="btree_not_null", copy=False)

    def _get_value_from_production(self, quantity, at_date=None):
        # Produsul rezultat intra in stoc la costul repartizat din consum, nu la costul lui curent
        self.ensure_one()
        if not self.mrp_simple_id:
            return super()._get_value_from_production(quantity, at_date)
        price_unit = self.product_uom._compute_price(self.price_unit, self.product_id.uom_id)
        value = quantity * price_unit
        return {
            "value": value,
            "quantity": quantity,
            "description": self.env._(
                "%(value)s for %(quantity)s %(unit)s from %(production)s",
                value=self.company_currency_id.format(value),
                quantity=quantity,
                unit=self.product_id.uom_id.name,
                production=self.mrp_simple_id.display_name,
            ),
        }
