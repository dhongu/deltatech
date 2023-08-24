# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProcessTest(models.Model):
    _name = "business.process.test"
    _description = "Business process Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    process_id = fields.Many2one(string="Process", comodel_name="business.process", required=True)
    tester_id = fields.Many2one(string="Tester", comodel_name="res.partner", required=True)
    date_start = fields.Date(string="Date start", required=True)
    date_end = fields.Date(string="Date end", required=True)


class BusinessProcessStepTest(models.Model):
    _name = "business.process.step.test"
    _description = "Business Process Step Test"

    process_test_id = fields.Many2one(string="Process Test", comodel_name="business.process.test", required=True)
    step_id = fields.Many2one(string="Step", comodel_name="business.process.step", required=True)
    result = fields.Selection([("ok", "Ok"), ("nok", "Nok")], string="Result", required=True)
    description = fields.Text(string="Description")
    date_start = fields.Date(string="Date start", required=True)
    date_end = fields.Date(string="Date end", required=True)
