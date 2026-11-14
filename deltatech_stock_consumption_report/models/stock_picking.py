from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_consumption = fields.Boolean(compute="_compute_is_consumption")
    consumption_purpose_id = fields.Many2one(
        "stock.consumption.purpose",
        string="Consumption purpose",
        check_company=True,
        help="What the consumed goods were used for (investments, own use...). "
        "The consumption report totals the value by purpose.",
    )

    @api.depends("location_dest_id.usage")
    def _compute_is_consumption(self):
        usages = self.env["stock.location"]._get_consumption_usages()
        for picking in self:
            picking.is_consumption = picking.location_dest_id.usage in usages
