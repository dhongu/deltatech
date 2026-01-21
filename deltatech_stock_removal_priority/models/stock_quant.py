# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    removal_priority = fields.Integer(
        compute="_compute_removal_priority", store=True, string="Removal Priority", default=1
    )

    @api.depends("product_id", "location_id")
    def _compute_removal_priority(self):
        internal_quants = self.filtered(lambda q: q.location_id.usage == "internal")
        (self - internal_quants).removal_priority = 0
        for quant in internal_quants:
            domain = [("product_id", "=", quant.product_id.id), ("location_in_id", "=", quant.location_id.id)]
            putaway_rule = self.env["stock.putaway.rule"].search(domain, limit=1, order="sequence asc")
            if putaway_rule:
                quant.removal_priority = putaway_rule.sequence
            else:
                quant.removal_priority = 0

    @api.model
    def _get_removal_strategy_domain_order(self, domain, removal_strategy, qty):
        if removal_strategy == "priority":
            domain = domain + [("removal_priority", ">", 0)]
            return domain, "removal_priority, location_id, id"
        return super()._get_removal_strategy_domain_order(domain, removal_strategy, qty)

    def _get_removal_strategy_sort_key(self, removal_strategy):
        key, reverse = super()._get_removal_strategy_sort_key(removal_strategy)
        if removal_strategy == "priority":

            def key(quant):
                return quant.removal_priority, quant.location_id.complete_name, quant.id

        return key, reverse
