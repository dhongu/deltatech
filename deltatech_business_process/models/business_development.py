# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessDevelopment(models.Model):
    _name = "business.development"
    _description = "Business Development"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Business area", comodel_name="business.area", required=True)
    type_id = fields.Many2one(string="Type", comodel_name="business.development.type", required=True)

    approved = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("rejected", "Rejected"), ("pending", "Pending")],
        string="Approved",
        default="draft",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("specification", "Specification"),
            ("development", "Development"),
            ("test", "Test"),
            ("production", "Production"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    date_start_fp = fields.Date(help="Start date functional specification")
    date_end_fp = fields.Date(help="End date functional specification")
    date_start_dev = fields.Date(help="Start date development")
    date_end_dev = fields.Date(help="End date development")
    date_start_test = fields.Date(help="Start date test")
    date_end_test = fields.Date(help="End date test")

    responsible_id = fields.Many2one(string="Consultant", comodel_name="res.partner")
    developer_id = fields.Many2one(string="Developer", comodel_name="res.partner")
    tester_id = fields.Many2one(string="Tester", comodel_name="res.partner")
    customer_id = fields.Many2one(string="Customer", comodel_name="res.partner")

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [
            (development.id, "{}{}".format(development.code and "[%s] " % development.code or "", development.name))
            for development in self
        ]
