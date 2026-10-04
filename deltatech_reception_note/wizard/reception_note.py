# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class ReceptionNoteCreate(models.TransientModel):
    _name = "reception.note.create"
    _description = "Reception Note Create Wizard"

    def do_create_reception_note(self):
        active_ids = self.env.context.get("active_ids", False)
        if active_ids:
            purchase_ids = self.env["purchase.order"].browse(active_ids)
        for purchase in purchase_ids:
            if not purchase.reception_type or purchase.reception_type == "normal":
                # keep the company, currency and fiscal position of the source order: the
                # prices and taxes copied below are expressed in them
                new_values = {
                    "state": "sent",
                    "company_id": purchase.company_id.id,
                    "currency_id": purchase.currency_id.id,
                    "fiscal_position_id": purchase.fiscal_position_id.id,
                    "partner_id": purchase.partner_id.id,
                    "partner_ref": purchase.partner_ref,
                    "date_approve": purchase.date_approve,
                    "date_planned": purchase.date_planned,
                    "origin": purchase.origin,
                    "reception_type": "rfq_only",
                    "picking_type_id": purchase.picking_type_id.id,
                    "payment_term_id": purchase.payment_term_id.id,
                }
                new_purchase = self.env["purchase.order"].with_company(purchase.company_id).create(new_values)

                for line in purchase.order_line:
                    if line.product_qty > line.qty_received:
                        diff = line.product_qty - line.qty_received
                        line_vals = {
                            "order_id": new_purchase.id,
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "product_qty": line.product_qty,
                            "uom_id": line.uom_id.id,
                            "price_unit": line.price_unit,
                            "tax_ids": [(6, 0, line.tax_ids.ids)],
                        }
                        new_line = self.env["purchase.order.line"].create(line_vals)
                        new_line.write({"product_qty": diff})
                        new_purchase.write({"order_line": [(4, new_line.id)]})

                for picking in purchase.picking_ids:
                    if picking.state == "assigned":
                        picking.action_cancel()
