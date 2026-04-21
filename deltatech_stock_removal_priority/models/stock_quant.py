# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.osv import expression


class StockQuant(models.Model):
    _inherit = "stock.quant"

    removal_priority = fields.Integer(
        compute="_compute_removal_priority",
        store=True,
        string="Removal Priority",
    )

    @api.depends("product_id", "location_id")
    def _compute_removal_priority(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        try:
            default_priority = int(get_param("stock.removal_priority.default", default="999"))
        except (ValueError, TypeError):
            default_priority = 999

        internal_quants = self.filtered(lambda q: q.location_id.usage == "internal")
        (self - internal_quants).removal_priority = default_priority

        if not internal_quants:
            return

        location_ids = internal_quants.mapped("location_id").ids
        product_ids = internal_quants.mapped("product_id").ids
        categ_ids = internal_quants.mapped("product_id.categ_id").ids

        # Un singur query pentru toate regulile relevante
        all_rules = self.env["stock.putaway.rule"].search(
            [
                ("location_out_id", "in", location_ids),
                "|",
                ("product_id", "in", product_ids),
                ("category_id", "in", categ_ids),
            ],
            order="sequence asc",
        )

        # Indexăm regulile: (location_out_id, product_id) -> sequence
        # și (location_out_id, category_id) -> sequence (doar prima, cea cu sequence minim)
        rules_by_product = {}
        rules_by_categ = {}
        for rule in all_rules:
            loc_id = rule.location_out_id.id
            if rule.product_id:
                key = (loc_id, rule.product_id.id)
                if key not in rules_by_product:
                    rules_by_product[key] = rule.sequence
            elif rule.category_id:
                key = (loc_id, rule.category_id.id)
                if key not in rules_by_categ:
                    rules_by_categ[key] = rule.sequence

        for quant in internal_quants:
            loc_id = quant.location_id.id
            product_key = (loc_id, quant.product_id.id)
            categ_key = (loc_id, quant.product_id.categ_id.id)

            if product_key in rules_by_product:
                quant.removal_priority = rules_by_product[product_key]
            elif categ_key in rules_by_categ:
                quant.removal_priority = rules_by_categ[categ_key]
            else:
                quant.removal_priority = default_priority

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == "priority":
            return "removal_priority, location_id, id"
        return super()._get_removal_strategy_order(removal_strategy)

    def _get_gather_domain(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
        domain = super()._get_gather_domain(product_id, location_id, lot_id, package_id, owner_id, strict)
        exclude_location_ids = self.env.context.get("exclude_location_ids")
        if exclude_location_ids:
            domain = expression.AND([domain, [("location_id", "not in", exclude_location_ids)]])
        return domain
