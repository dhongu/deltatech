# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved


from odoo import fields, models


class PaymentForecast(models.Model):
    _name = "payment.forecast"
    _description = "Payment forecast"
    _order = "id desc"

    days = fields.Char(string="Days")
    partner_id = fields.Many2one("res.partner", string="Partner")
    move_id = fields.Many2one("account.move", string="Invoice")

    currency_id = fields.Many2one("res.currency", string="Currency")
    move_date = fields.Date(string="Invoice date")
    move_due_date = fields.Date(string="Invoice due date")
    move_amount = fields.Monetary("Invoice amount", currency_field="currency_id")
    journal_id = fields.Many2one("account.journal", string="Journal")
    move_type = fields.Selection([("incoming", "Incoming"), ("outgoing", "Outgoing")])

    # will be used for theoretical amount reporting
    move_amount_residual = fields.Monetary("Invoice amount residual", currency_field="currency_id")

    # will be used with average payment time factor
    payment_amount_forecasted = fields.Monetary("Payment amount", currency_field="currency_id")
