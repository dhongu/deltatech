# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.tools.misc import clean_context


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_post(self):
        sale_invoices = self.filtered(
            lambda inv: inv.move_type == "out_invoice" and inv.state == "draft" and inv.journal_id.invoice_delivery
        )
        if "pos_order_ids" in self._fields:
            sale_invoices = sale_invoices.filtered(lambda inv: not inv.pos_order_ids)
        if sale_invoices:
            sale_invoices.add_to_sale()
            sale_invoices.delivery_form_stock()
        return super().action_post()

    def _get_lines_to_deliver(self):
        """Storable products of the invoice that are not linked to a sale order"""
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda line: not line.sale_line_ids
            and line.display_type == "product"
            and line.product_id.type == "consu"
            and line.product_id.is_storable
        )

    def _prepare_sale_order_from_invoice(self):
        self.ensure_one()
        invoice_date = self.invoice_date or fields.Date.context_today(self)
        return {
            "partner_id": self.partner_id.id,
            "partner_invoice_id": self.partner_id.id,
            "partner_shipping_id": (self.partner_shipping_id or self.partner_id).id,
            "date_order": fields.Datetime.to_datetime(invoice_date),
            "client_order_ref": self.ref,
            "fiscal_position_id": self.fiscal_position_id.id,
            "currency_id": self.currency_id.id,
            "user_id": self.invoice_user_id.id,
            "team_id": self.team_id.id,
            "company_id": self.company_id.id,
            "from_invoice_id": self.id,
        }

    def _prepare_sale_order_line_from_invoice_line(self, line, sale_order):
        return {
            "order_id": sale_order.id,
            "sequence": line.sequence,
            "product_id": line.product_id.id,
            "product_uom_id": line.product_uom_id.id,
            "name": line.name,
            "product_uom_qty": line.quantity,
            "price_unit": line.price_unit,
            "discount": line.discount,
            "tax_ids": [(6, 0, line.tax_ids.ids)],
        }

    def _get_invoice_delivery_env(self):
        # the invoice context carries default_move_type, which is also a field of the delivery
        return self.env(context=clean_context(self.env.context))

    def add_to_sale(self):
        """The storable lines without a sale order are added to a new sale order, which is confirmed"""
        env = self._get_invoice_delivery_env()
        for invoice in self:
            lines_without_sale = invoice._get_lines_to_deliver()
            if not lines_without_sale:
                continue
            sale_order = env["sale.order"].create(invoice._prepare_sale_order_from_invoice())
            sale_order._check_invoice_delivery_steps()
            for line in lines_without_sale:
                line_so = env["sale.order.line"].create(
                    invoice._prepare_sale_order_line_from_invoice_line(line, sale_order)
                )
                line.write({"sale_line_ids": [(6, 0, line_so.ids)]})
            sale_order.action_confirm()
            sale_order.message_post_with_source(
                "mail.message_origin_link",
                render_values={"self": sale_order, "origin": invoice},
                subtype_xmlid="mail.mt_note",
            )
            invoice.message_post(body=self.env._("The sale order %s was generated.", sale_order._get_html_link()))

    def delivery_form_stock(self):
        env = self._get_invoice_delivery_env()
        for invoice in self:
            sale_orders = invoice.invoice_line_ids.sale_line_ids.order_id
            # the delivery is validated only for the sale orders generated from this invoice
            sale_orders = sale_orders.filtered(lambda order: order.from_invoice_id == invoice)
            invoice_date = invoice.invoice_date or fields.Date.context_today(invoice)
            sale_orders.with_env(env).delivery_from_stock(invoice_date)
