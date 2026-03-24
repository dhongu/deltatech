# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, Command


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    bom_base_type = fields.Selection(related="bom_id.base_type")

    def _compute_derived_bom(self):
        for production in self:
            if not (production.bom_id and production.bom_id.base_type == "base" and production.product_id):
                # check if there is a base bom for this product
                domain = [("product_tmpl_id", "=", production.product_tmpl_id.id), ("base_type", "=", "base")]
                base_bom = self.env["mrp.bom"].search(domain, limit=1)
                if not base_bom:
                    continue

            domain = [("product_id", "=", production.product_id.id), ("base_type", "=", "derived")]
            derived_bom = self.env["mrp.bom"].search(domain, limit=1)
            if not derived_bom:
                domain = [("product_tmpl_id", "=", production.product_tmpl_id.id), ("base_type", "=", "derived")]
                variant_count = self.env["mrp.bom"].search_count(domain) + 1
                derived_bom = self.env["mrp.bom"].create(
                    {
                        "product_tmpl_id": production.product_tmpl_id.id,
                        "product_id": production.product_id.id,
                        "base_type": "derived",
                        "code": f"D{variant_count}",
                    }
                )
            derived_bom.recompute_from_base()
            production.move_raw_ids = [Command.clear()]
            production.bom_id = derived_bom

    @api.onchange("product_id")
    def _change_product_id(self):
        self._compute_derived_bom()

    def action_compute_derived_bom(self):
        self._compute_derived_bom()

    def action_confirm(self):
        for production in self:
            if production.bom_id.base_type != "normal":
                production.bom_id.recompute_from_base()

        return super().action_confirm()
