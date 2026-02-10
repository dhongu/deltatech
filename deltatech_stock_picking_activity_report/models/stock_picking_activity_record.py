from odoo import fields, models


class StockPickingActivityRecord(models.Model):
    _name = "stock.picking.activity.record"
    _description = "Stock Picking Activity Record"

    picking_id = fields.Many2one("stock.picking", string="Picking", required=True, ondelete="cascade")
    change_date = fields.Date(string="Change Date", default=fields.Date.context_today, required=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("waiting", "Waiting Another Operation"),
            ("confirmed", "Waiting"),
            ("assigned", "Ready"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="State",
    )

    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user, required=True)

    chatter_message = fields.Boolean(string="Chatter Message")
    has_validated = fields.Boolean(string="Has Validated")
    awb_generated = fields.Boolean(string="AWB Generated")
    exit_product_number = fields.Float(string="Exit Product Number")
    entry_product_number = fields.Float(string="Entry Product Number")
    internal_product_number = fields.Float(string="Internal Product Number")
    activity_log = fields.Text(string="Activity Log")
