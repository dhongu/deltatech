# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_post(self):
        sale_invoices = self.filtered(lambda inv: inv.move_type == "out_invoice")
        if sale_invoices:
            sale_invoices.add_to_sale()
            sale_invoices.delivery_form_stock()
        return super(AccountInvoice, self).action_post()

    def add_to_sale(self):
        for invoice in self:
            # exista o comanda de achizitie legata de aceasta factura ?
            sale_order = self.env["sale.order"]
            for line in invoice.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    sale_order |= sale_line.order_id

            # am gasit linii care nu sunt in comanda de vanzare
            lines_without_sale = invoice.invoice_line_ids.filtered(lambda line: not line.sale_line_ids)
            # doar pentru prousele stocabile
            lines_without_sale = lines_without_sale.filtered(lambda line: line.product_id.type == "product")
            if lines_without_sale:

                if len(sale_order) != 1:
                    sale_order = (
                        self.env["sale.order"]
                        .with_context(default_move_type=False)
                        .create(
                            {
                                "partner_id": invoice.partner_id.id,
                                "date_order": invoice.invoice_date or fields.Date.context_today(invoice),
                                "client_order_ref": invoice.ref,
                                "fiscal_position_id": invoice.fiscal_position_id.id,
                                "from_invoice_id": invoice.id,
                                "currency_id": invoice.currency_id.id,  # Preluare Moneda in comanda de achizitie
                            }
                        )
                    )

                for line in lines_without_sale:
                    line_so = self.env["sale.order.line"].create(
                        {
                            "order_id": sale_order.id,
                            "sequence": line.sequence,
                            "product_id": line.product_id.id,
                            "product_uom": line.product_uom_id.id,
                            "name": line.name,
                            "price_unit": line.price_unit,
                            "product_uom_qty": line.quantity,
                            "tax_id": [(6, 0, line.tax_ids.ids)],
                        }
                    )
                    line_so.write({"product_uom_qty": line.quantity})
                    line.write(
                        {
                            "sale_line_ids": [(6, 0, line_so.ids)],
                            # 'purchase_id': purchase_order.id,
                        }
                    )
                sale_order.action_confirm()  # confirma comanda de vanzare
                sale_order.message_post_with_view(
                    "mail.message_origin_link",
                    values={"self": sale_order, "origin": invoice},
                    subtype_id=self.env.ref("mail.mt_note").id,
                )
                link = (
                    "<a href=# data-oe-model=sale.order data-oe-id="
                    + str(sale_order.id)
                    + ">"
                    + sale_order.name
                    + "</a>"
                )
                message = _("The sale order %s was generated.") % link
                invoice.message_post(body=message)

    def delivery_form_stock(self):
        sale_orders = self.env["sale.order"]
        for invoice in self:
            # trebuie sa determin care este cantitatea care trebuie sa fie receptionata
            for line in invoice.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    sale_orders |= sale_line.order_id

        # doar pentru comenzile generate din factura se face receptia
        sale_orders = sale_orders.filtered(lambda order: order.from_invoice_id)
        sale_orders.with_context(default_move_type=False, default_journal_id=False).delivery_from_stock()
