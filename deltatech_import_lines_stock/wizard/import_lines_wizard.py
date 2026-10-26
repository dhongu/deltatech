# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ImportLinesWizard(models.TransientModel):
    _inherit = "import.lines.wizard"

    location_id = fields.Many2one(
        "stock.location",
        string="Counted Location",
        domain="[('usage', '=', 'internal')]",
        help="Location of the inventory count.",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if defaults.get("res_model") == "stock.quant" and "location_id" in fields_list:
            warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
            defaults.setdefault("location_id", warehouse.lot_stock_id.id)
        return defaults
