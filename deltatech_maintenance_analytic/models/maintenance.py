# ©  2008-2020  Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic",
        help="Link this equipment to an analytic account if you need financial management on equipment. ",
        ondelete="restrict",
        required=False,
        auto_join=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("analytic_account_id"):
                vals["analytic_account_id"] = self.env["account.analytic.account"].create({"name": vals["name"]}).id

        return super(MaintenanceEquipment, self).create(vals_list)
