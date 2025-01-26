# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"

    def _export_invoice_vals(self, invoice):
        vals_list = super()._export_invoice_vals(invoice)

        pickings = self.env["stock.picking"]
        for line in invoice.invoice_line_ids:
            for sale_line in line.sale_line_ids:
                for move in sale_line.move_ids:
                    if move.picking_id.state == "done":
                        pickings |= move.picking_id
        if pickings:
            names = pickings.mapped("name")
            vals_list["vals"]["despatch_advice"] = ", ".join(names)
        return vals_list
