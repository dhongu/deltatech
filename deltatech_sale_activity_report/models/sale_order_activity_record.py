# models/sale_order_activity_record.py
from odoo import fields, models


class SaleOrderActivityRecord(models.Model):
    _name = "sale.order.activity.record"
    _description = "Sale Order Activity Record"

    sale_order_id = fields.Many2one("sale.order", string="Sale Order", required=True, ondelete="cascade")
    change_date = fields.Date(string="Change Date", default=fields.Datetime.now, required=True)
    state = fields.Selection(
        selection=[
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="State",
    )
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user, required=True)
