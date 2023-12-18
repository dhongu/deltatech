# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessTransaction(models.Model):
    _name = "business.transaction"
    _description = "Business transaction"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    area_id = fields.Many2one("business.area", string="Business Area")
    transaction_type = fields.Selection(
        [("md", "Master Data"), ("tr", "Transaction"), ("rp", "Report"), ("ex", "Extern")],
        string="Transaction Type",
        required=True,
        default="tr",
    )

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [
            (process.id, "{}{}".format(process.code and "[%s] " % process.code or "", process.name)) for process in self
        ]
