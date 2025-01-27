# ©  2024 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    group_id = fields.Many2one("procurement.group", string="Group")

    def _prepare_run_values(self):
        # OVERRIDE
        if not self.group_id:
            return super()._prepare_run_values()

        domain = [("group_id", "=", self.group_id.id), ("state", "=", "done")]
        move_ids = self.env["stock.move"].search(domain, limit=1)
        if move_ids:
            raise UserError(_("The replenishment has already been done for this group."))

        values = {
            "warehouse_id": self.warehouse_id,
            "route_ids": self.route_id,
            "date_planned": self.date_planned,
            "group_id": self.group_id,
        }
        return values
