from odoo import api, fields, models


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
    chatter_message_count = fields.Integer(
        string="Chatter Message Count",
        compute="_compute_chatter_message_count",
        store=True,
    )
    has_validated = fields.Boolean(string="Has Validated")
    has_validated_count = fields.Integer(
        string="Validated Count",
        compute="_compute_has_validated_count",
        store=True,
    )
    awb_generated = fields.Boolean(string="AWB Generated")
    exit_product_number = fields.Float(string="Exit Product Number")
    entry_product_number = fields.Float(string="Entry Product Number")
    internal_product_number = fields.Float(string="Internal Product Number")
    activity_log = fields.Text(string="Activity Log")

    @api.depends("has_validated")
    def _compute_has_validated_count(self):
        for rec in self:
            rec.has_validated_count = 1 if rec.has_validated else 0

    @api.depends("chatter_message")
    def _compute_chatter_message_count(self):
        for rec in self:
            rec.chatter_message_count = 1 if rec.chatter_message else 0
