# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    simple_mrp_picking_ids = fields.One2many("stock.picking", "sale_simple_mrp_id", string="Simple MRP Transfers")
    simple_mrp_count = fields.Integer(string="Count MRP Simple", compute="_compute_simple_mrp_picking_ids")

    @api.depends("simple_mrp_picking_ids")
    def _compute_simple_mrp_picking_ids(self):
        for order in self:
            order.simple_mrp_count = len(order.simple_mrp_picking_ids) / 2

    def action_view_mrp(self):
        self.ensure_one()
        mrps = self.env["mrp.simple"].search([("sale_order_id", "=", self.id)], limit=1)
        if mrps:
            mrp_id = mrps[0].id
        return {
            "res_id": mrp_id,
            "target": "current",
            "name": _("Simple production"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mrp.simple",
            "view_id": self.env.ref("deltatech_mrp_simple.view_mrp_simple_form").id,
            "context": {},
            "type": "ir.actions.act_window",
        }

    def add_multiple_lines(self):
        pass
