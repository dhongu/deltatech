# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def check_authorization_transfer(self):
        group_ext_id = "deltatech_rec_access.group_stock_no_transfer"
        res = self.env["res.users"].has_group(group_ext_id)
        if res:
            for picking in self:
                if picking.location_id.user_id and picking.location_id.user_id.id != self.env.user.id:
                    raise UserError(_("You can not have authorization transfer stock from this location."))
                if picking.location_dest_id.usage not in ["customer", "production"]:
                    raise UserError(
                        _(
                            "You can not have authorization transfer stock to this location.\n"
                            + "The destination location selected is not a client or production location"
                        )
                    )
        return True

    def do_enter_transfer_details(self):
        self.check_authorization_transfer()
        return super(StockPicking, self).do_enter_transfer_details()

    def do_transfer(self):
        self.check_authorization_transfer()
        return super(StockPicking, self).do_transfer()
