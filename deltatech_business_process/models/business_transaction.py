# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

from ..tools.display_name import code_display_name


class BusinessTransaction(models.Model):
    _name = "business.transaction"
    _description = "Business transaction"
    _rec_names_search = ["name", "code"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    area_id = fields.Many2one("business.area", string="Business Area")
    transaction_type = fields.Selection(
        [
            ("md", "Master Data"),
            ("tr", "Transaction"),
            ("rp", "Report"),
            ("ex", "Extern"),
        ],
        string="Transaction Type",
        required=True,
        default="tr",
    )

    @api.depends("code", "name")
    @api.depends_context("formatted_display_name")
    def _compute_display_name(self):
        for transaction in self:
            transaction.display_name = code_display_name(transaction)
