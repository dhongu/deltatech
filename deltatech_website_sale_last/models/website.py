# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def reopen_last_order(self):
        partner = self.env.user.partner_id
        last_website_so_id = self.env["sale.order"].search(
            [
                ("partner_id", "=", partner.id),
                ("website_id", "=", self.id),
                ("state", "=", "sent"),
            ],
            order="write_date desc",
            limit=1,
        )
        if last_website_so_id:
            last_website_so_id.action_cancel()
            last_website_so_id.action_draft()
            request.session["sale_order_id"] = last_website_so_id.id

    # redeschiderea auatomata a comenzii
    # def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
    #
    #     self.ensure_one()
    #     partner = self.env.user.partner_id
    #     sale_order_id = request.session.get('sale_order_id')
    #     if not sale_order_id and not self.env.user._is_public():
    #         last_order = partner.last_website_so_id
    #         if not last_order and force_create:
    #             self.reopen_last_order()
    #             force_create = False
    #
    #     sale_order = super(Website, self).sale_get_order(force_create, code, update_pricelist, force_pricelist)
    #
    #     return sale_order
