# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessOpenIssue(models.Model):
    _name = "business.open.issue"
    _description = "Business Open Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Business area", comodel_name="business.area")
    responsible_id = fields.Many2one(string="Responsible", comodel_name="res.partner")
    customer_id = fields.Many2one(string="Customer", comodel_name="res.partner")
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("closed", "Closed")], string="State", default="draft"
    )
    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)
    process_id = fields.Many2one(string="Process", comodel_name="business.process")

    date = fields.Date(string="Date", required=True)
    deadline = fields.Date(string="Deadline")
    closed_date = fields.Date(string="Closed Date")

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [(item.id, "{}{}".format(item.code and "[%s] " % item.code or "", item.name)) for item in self]
