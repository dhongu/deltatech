from odoo import api, fields, models


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

        # The comparison uses the native qty_available, so the search applies the same
        # scope as the computed field: allowed companies and the warehouse/location
        # from the context. Only templates with a minimum set are candidates.
        templates = self.with_context(active_test=False).search([("total_minimum", ">", 0)])
        ids = templates.filtered(lambda t: t.qty_available < t.total_minimum).ids

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
