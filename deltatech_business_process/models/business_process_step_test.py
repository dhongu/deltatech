# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProcessStepTest(models.Model):
    _name = "business.process.step.test"
    _description = "Business Process Step Test"

    process_test_id = fields.Many2one(
        string="Process Test", comodel_name="business.process.test", required=True, ondelete="cascade"
    )
    step_id = fields.Many2one(string="Step", comodel_name="business.process.step", required=True)
    process_id = fields.Many2one(
        string="Process", comodel_name="business.process", related="step_id.process_id", store=True
    )

    sequence = fields.Integer(string="Sequence", related="step_id.sequence", store=True)
    name = fields.Char(string="Name", related="step_id.name", store=True)
    description = fields.Text(string="Description", related="step_id.description", store=True)
    transaction_id = fields.Many2one(
        string="Transaction", comodel_name="business.transaction", related="step_id.transaction_id", store=True
    )
    responsible_id = fields.Many2one(
        string="Responsible", comodel_name="res.partner", domain="[('is_company', '=', False)]", store=True
    )

    result = fields.Selection(
        [
            ("draft", "Draft"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        string="Result",
        default="draft",
    )
    data_used = fields.Text(string="Data used")
    data_result = fields.Text(string="Data result")

    date_start = fields.Date(string="Date start")
    date_end = fields.Date(string="Date end")
    observation = fields.Text(string="Observation")

    feedback_by_id = fields.Many2one("res.partner", string="", domain="[('is_company', '=', False)]")
    feedback_text = fields.Text(string="Feedback")
    feedback_date = fields.Date(string="Feedback date")
    feedback_state = fields.Selection(
        [("draft", "Draft"), ("ok", "Ok"), ("not_ok", "Not ok")], string="Feedback state", default="draft"
    )
