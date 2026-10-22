# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleMarginReport(models.Model):
    _inherit = "sale.margin.report"

    manufacturer_id = fields.Many2one("res.partner", string="Manufacturer", readonly=True)

    def _select(self):
        return super()._select() + ", manufacturer_id"

    def _sub_select(self):
        return super()._sub_select() + ", t.manufacturer_id"

    def _group_by(self):
        return super()._group_by() + ", t.manufacturer_id"

    def _prepare_extra_source(self, source):
        # the other sources (the orders of the point of sale) get the manufacturer of their product,
        # else their rows fall under "None"; looked up from the product, the sources have no
        # common alias for the product template
        source = super()._prepare_extra_source(source)
        product = source["columns"].get("product_id")
        if not product:
            return source
        manufacturer = f"""(
            select pt.manufacturer_id
              from product_product pp
              join product_template pt on (pt.id = pp.product_tmpl_id)
             where pp.id = {product}
        )"""
        return dict(source, columns=dict(source["columns"], manufacturer_id=manufacturer))
