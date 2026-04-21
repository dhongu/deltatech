# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


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
        default_priority = get_param("stock.removal_priority.default", default="999")
        default_priority = safe_eval(default_priority)

        internal_quants = self.filtered(lambda q: q.location_id.usage == "internal")
        (self - internal_quants).removal_priority = default_priority
        for quant in internal_quants:
            # Căutăm regulile atât după location_out_id cât și după location_in_id pentru
            # a acoperi ambele scenarii de configurare.
            domain_product = [
                ("product_id", "=", quant.product_id.id),
                ("location_out_id", "=", quant.location_id.id),
            ]
            putaway_rule = self.env["stock.putaway.rule"].search(domain_product, limit=1, order="sequence asc")
            if not putaway_rule:
                domain_categ = [
                    ("category_id", "=", quant.product_id.categ_id.id),
                    ("location_out_id", "=", quant.location_id.id),
                ]
                putaway_rule = self.env["stock.putaway.rule"].search(domain_categ, limit=1, order="sequence asc")

            if putaway_rule:
                quant.removal_priority = putaway_rule.sequence
            else:
                quant.removal_priority = default_priority

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == "priority":
            return "removal_priority, location_id, id"
        return super()._get_removal_strategy_order(removal_strategy)

    # @api.model
    # def _get_removal_strategy_domain_order(self, domain, removal_strategy, qty):
    #     exclude_location_ids = self.env.context.get("exclude_location_ids")
    #     if exclude_location_ids:
    #         domain = expression.AND([domain, [("location_id", "not in", exclude_location_ids)]])
    #
    #     if removal_strategy == "priority":
    #         # domain = domain + [("removal_priority", ">=", 0)]
    #         return domain, "removal_priority, location_id, id"
    #     return super()._get_removal_strategy_domain_order(domain, removal_strategy, qty)
    #
    # def _get_removal_strategy_sort_key(self, removal_strategy):
    #     key, reverse = super()._get_removal_strategy_sort_key(removal_strategy)
    #     if removal_strategy == "priority":
    #
    #         def key(quant):
    #             return quant.removal_priority, quant.location_id.complete_name, quant.id
    #
    #     return key, reverse
