# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    merged_into_id = fields.Many2one(
        "sale.order",
        string="Merged Into",
        copy=False,
        readonly=True,
        index="btree_not_null",
        help="The quotation that took over the lines of this one when they were merged.",
    )
    merged_from_ids = fields.One2many(
        "sale.order",
        "merged_into_id",
        string="Merged From",
        copy=False,
        readonly=True,
    )

    def action_merge_orders(self):
        wizard = self.env["sale.order.merge"].with_context(active_model="sale.order", active_ids=self.ids)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Merge orders"),
            "res_model": "sale.order.merge",
            "view_mode": "form",
            "target": "new",
            "context": dict(wizard.env.context),
        }
