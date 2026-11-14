# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError


class PricelistBulkFormula(models.TransientModel):
    _name = "pricelist.bulk.formula"
    _inherit = ["pricelist.formula.mixin"]
    _description = "Apply the Same Formula to Many Pricelist Rules"

    item_ids = fields.Many2many("product.pricelist.item", string="Rules")
    item_count = fields.Integer(compute="_compute_item_count", string="Number of Rules")
    change_price = fields.Boolean(string="Change the Price Computation", default=True)
    change_min_quantity = fields.Boolean(string="Change the Min. Quantity")
    min_quantity = fields.Float(string="Min. Quantity", digits="Product Unit")
    change_dates = fields.Boolean(string="Change the Validity Period")
    date_start = fields.Datetime(string="Start Date")
    date_end = fields.Datetime(string="End Date")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self.env.context
        if context.get("active_model") == "product.pricelist.item" and context.get("active_ids"):
            res["item_ids"] = [fields.Command.set(context["active_ids"])]
        return res

    @api.depends("item_ids")
    def _compute_item_count(self):
        for wizard in self:
            wizard.item_count = len(wizard.item_ids)

    def _get_write_vals(self):
        self.ensure_one()
        vals = {}
        if self.change_price:
            vals.update(self._get_formula_vals())
        if self.change_min_quantity:
            vals["min_quantity"] = self.min_quantity
        if self.change_dates:
            vals.update(date_start=self.date_start, date_end=self.date_end)
        return vals

    def action_apply(self):
        self.ensure_one()
        if not self.item_ids:
            raise UserError(self.env._("Select at least one pricelist rule."))
        vals = self._get_write_vals()
        if not vals:
            raise UserError(self.env._("Choose what to change on the selected rules."))
        self._check_base_pricelist(vals, self.item_ids.pricelist_id)
        self.item_ids.write(vals)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": self.env._("%s rules changed.", len(self.item_ids)),
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
