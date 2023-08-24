# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProcess(models.Model):
    _name = "business.process"
    _description = "Business process"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Area", comodel_name="business.area", required=True)
    step_ids = fields.One2many(string="Steps", comodel_name="business.process.step", inverse_name="process_id")
    responsible_id = fields.Many2one(string="Process Responsible", comodel_name="res.partner", required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("test", "Test"), ("approved", "Approved")], string="State", default="draft"
    )
    approved_id = fields.Many2one(string="Approved by", comodel_name="res.partner")
    tests_ids = fields.One2many(string="Tests", comodel_name="business.process.test", inverse_name="process_id")
    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)


class BusinessProcessStep(models.Model):
    _name = "business.process.step"
    _description = "Business process step"
    _order = "sequence"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    process_id = fields.Many2one(string="Process", comodel_name="business.process", required=True)
    sequence = fields.Integer(string="Sequence", required=True)
    responsible_id = fields.Many2one(string="Responsible Step", comodel_name="res.partner", required=True)
    development_ids = fields.Many2one(
        string="Development Type", comodel_name="business.development.type", required=True
    )
