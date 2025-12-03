# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    notice = fields.Boolean()

    def action_view_sale_invoice(self):
        if self.sale_id:
            action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
            field_notice = False
            if "notice" in self.env["stock.picking"]._fields:
                field_notice = "notice"
            if "l10n_ro_notice" in self.env["stock.picking"]._fields:
                field_notice = "l10n_ro_notice"

            action["context"] = {
                "active_id": self.sale_id.id,
                "active_ids": self.sale_id.ids,
                field_notice: True,
            }
            return action
