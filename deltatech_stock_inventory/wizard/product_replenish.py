# ©  2024 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    # NOTĂ O19: modelul `procurement.group` și `stock.move.group_id` au fost eliminate
    # în Odoo 19, deci garda anti-duplicare pe grup de procurement (prezentă în 18.0)
    # nu este portabilă. Lăsată dezactivată intenționat până la un echivalent O19.
    # group_id = fields.Many2one("procurement.group", string="Group")
    #
    # def _prepare_run_values(self):
    #     # OVERRIDE
    #     if not self.group_id:
    #         return super()._prepare_run_values()
    #
    #     domain = [("group_id", "=", self.group_id.id), ("state", "=", "done")]
    #     move_ids = self.env["stock.move"].search(domain, limit=1)
    #     if move_ids:
    #         raise UserError(self.env._("The replenishment has already been done for this group."))
    #
    #     values = {
    #         "warehouse_id": self.warehouse_id,
    #         "route_ids": self.route_id,
    #         "date_planned": self.date_planned,
    #         "force_uom": True,
    #         "group_id": self.group_id,
    #     }
    #     return values
