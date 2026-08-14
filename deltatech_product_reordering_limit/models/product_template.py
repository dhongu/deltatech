from odoo import api, fields, models
from odoo.tools import SQL


class ProductTemplate(models.Model):
    _inherit = "product.template"

    total_minimum = fields.Float(string="Total Minimum", default=0.0)
    total_maximum = fields.Float(string="Total Maximum", default=0.0)

    def _search_is_below_min(self, operator, value):
        # Odoo 19 normalizes boolean domains to the `in` / `not in` operators with
        # a `[True]` value (see odoo/orm/domains.py::_optimize_boolean_in), so the
        # search method must accept them directly.
        if operator not in ("in", "not in") or set(value) != {True}:
            raise NotImplementedError("Unsupported operator or value for _search_is_below_min")

        # We need to find templates where qty_available < total_minimum.
        # Since we can't do this easily in a domain with a computed field vs another field,
        # and a raw SQL might miss Odoo's complex stock logic (locations, etc.),
        # but for a general "Below Minimum" filter, we can use a reasonable SQL approximation
        # that aggregates variant quantities to the template level.

        # We use a subquery to sum quantities from stock_quant grouped by product,
        # then join with product_product to group by template.
        # We only count internal locations as per requirement.
        rows = self.env.execute_query(
            SQL(
                """
            SELECT pt.id
            FROM product_template pt
            JOIN (
                SELECT pp.product_tmpl_id, SUM(sq.qty) as total_qty_available
                FROM product_product pp
                LEFT JOIN (
                    SELECT sq.product_id, SUM(sq.quantity) as qty
                    FROM stock_quant sq
                    JOIN stock_location sl ON sl.id = sq.location_id
                    WHERE sl.usage = 'internal'
                    GROUP BY sq.product_id
                ) sq ON sq.product_id = pp.id
                GROUP BY pp.product_tmpl_id
            ) t_qty ON t_qty.product_tmpl_id = pt.id
            WHERE pt.total_minimum > 0 AND COALESCE(t_qty.total_qty_available, 0.0) < pt.total_minimum
        """
            )
        )
        ids = [r[0] for r in rows]

        return [("id", operator, ids)]

    is_below_min = fields.Boolean(
        string="Is Below Minimum", compute="_compute_is_below_min", search="_search_is_below_min"
    )

    @api.depends("qty_available", "total_minimum")
    def _compute_is_below_min(self):
        for template in self:
            # qty_available on template level in Odoo 18 (when called without specific context)
            # aggregates qty_available of all its variants.
            # Product variants' qty_available already filters by internal locations by default.
            template.is_below_min = template.total_minimum > 0 and template.qty_available < template.total_minimum
