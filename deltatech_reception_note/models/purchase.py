# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    reception_type = fields.Selection(
        [("normal", "Normal"), ("rfq_only", "RFQ Only"), ("note", "Reception Note")], string="Type", default="normal"
    )
    delivery_note_no = fields.Char(string="Delivery Note No")
    is_empty = fields.Boolean(string="Is empty", default=False)
    date_sent = fields.Datetime(string="Date sent")
    ignore_quantities = fields.Boolean(
        string="Ignore quantities",
        default=False,
        help="If checked, quantities bigger than those found on rfq's are forced for reception",
    )
    rfq_consumption_ids = fields.One2many(
        "purchase.reception.note.consumption",
        "note_id",
        string="RFQ consumption",
        readonly=True,
        copy=False,
    )

    def action_rfq_send(self):
        if self.reception_type != "note":
            return super().action_rfq_send()

    def set_sent(self):
        self.ensure_one()
        self.write({"state": "sent", "date_sent": fields.Datetime.now()})

    def button_confirm(self):
        orders = self
        for order in self:
            if order.reception_type == "rfq_only":
                orders -= order
        if not orders:
            raise UserError(self.env._("Unable to confirm"))

        # Confirmarea standard sare peste comenzile care nu sunt in draft/sent; doar notele care se
        # confirma acum consuma din RFQ-uri, altfel o reconfirmare ar scadea a doua oara.
        notes_to_reduce = orders.filtered(lambda o: o.reception_type == "note" and o.state in ("draft", "sent"))

        res = super(PurchaseOrder, orders).button_confirm()

        for order in notes_to_reduce:
            if order.ignore_quantities:
                lines = order.with_company(order.company_id).reduce_from_rfq()
                if lines:
                    # the translated templates are trusted HTML; the product data is escaped by format()
                    message = Markup(self.env._("Quantities forced on this reception note:<br />"))
                    for line in lines:
                        message += Markup(
                            self.env._("Product [{product_code}]{product_name}: quantity: {quantity} {uom}<br />")
                        ).format(
                            product_code=line["product_id"].default_code,
                            product_name=line["product_id"].name,
                            quantity=line["product_qty"],
                            uom=line["uom"].name,
                        )
                    order.message_post(body=message)
            else:
                order.with_company(order.company_id).reduce_from_rfq()
        return res

    def button_cancel(self):
        notes = self.filtered(lambda o: o.reception_type == "note" and o.rfq_consumption_ids)
        res = super().button_cancel()
        # Anularea standard poate fi refuzata (ex. facturi validate); restituim doar dupa ce a reusit.
        notes.filtered(lambda o: o.state == "cancel").restore_to_rfq()
        return res

    def restore_to_rfq(self):
        """Give back to the RFQ lines the quantities consumed by these reception notes.

        The quantity already received (validated receipts, also partial ones with a backorder) stays in
        stock after the cancellation, so it is no longer expected from the vendor and is not given back:
        it is kept on the oldest consumed RFQ lines, the ones the note drew from first.
        """
        for note in self:
            consumptions = note.rfq_consumption_ids.sorted("id")
            not_restored = False
            for product in consumptions.rfq_line_id.product_id:
                product_uom = product.uom_id
                received = sum(
                    line.product_uom_id._compute_quantity(line.qty_received, product_uom, round=False)
                    for line in note.order_line.filtered(lambda li, p=product: li.product_id == p)
                )
                for consumption in consumptions.filtered(lambda c, p=product: c.rfq_line_id.product_id == p):
                    rfq_line = consumption.rfq_line_id
                    consumed = rfq_line.product_uom_id._compute_quantity(consumption.quantity, product_uom, round=False)
                    kept = min(consumed, max(received, 0.0))
                    received -= kept
                    if not product_uom.is_zero(kept):
                        not_restored = True
                    to_restore = rfq_line.product_uom_id.round(
                        consumption.quantity - product_uom._compute_quantity(kept, rfq_line.product_uom_id, round=False)
                    )
                    if to_restore > 0:
                        rfq_line.write({"product_qty": rfq_line.product_qty + to_restore})
                        rfq_line.order_id.filtered("is_empty").write({"is_empty": False})
            if not_restored:
                note.message_post(
                    body=self.env._(
                        "The quantities already received on this reception note were not given back to the "
                        "RFQs: the goods are in stock."
                    )
                )
            consumptions.unlink()

    def reduce_from_rfq(self):
        self.ensure_one()
        # only the sent RFQs of the reception note company may be consumed
        domain = [
            ("partner_id", "=", self.partner_id.id),
            ("reception_type", "=", "rfq_only"),
            ("state", "=", "sent"),
            ("is_empty", "=", False),
            ("company_id", "=", self.company_id.id),
        ]
        rfq_orders = self.env["purchase.order"].search(domain, order="id")
        found_errors = []
        quantity_errors = []
        lines_to_add = []
        consumption_vals = []
        for line in self.order_line:
            # Nota si RFQ-urile pot fi in unitati diferite (nota in bucati, RFQ in baxuri): consumul
            # se calculeaza in unitatea produsului si se scrie inapoi in unitatea fiecarei linii RFQ.
            product_uom = line.product_id.uom_id
            line_qty = line.product_uom_id._compute_quantity(line.product_qty, product_uom, round=False)
            quantity = line_qty
            domain = [
                ("order_id", "in", rfq_orders.ids),
                ("product_id", "=", line.product_id.id),
                ("product_qty", ">", 0.0),
            ]
            rfq_lines = self.env["purchase.order.line"].search(domain)
            rfq_lines = rfq_lines.sorted(key=lambda unsorted_rfq_line: unsorted_rfq_line.date_order)
            if not rfq_lines:
                if not self.ignore_quantities:
                    found_errors.append(
                        self.env._(
                            "The product [%(default_code)s]%(name)s is not found in a sent RFQ. "
                            "Tick 'Ignore quantities' to receive it anyway.",
                            default_code=line.product_id.default_code,
                            name=line.product_id.name,
                        )
                    )

            if not found_errors:
                # check for quantities without writing the rfq lines
                for rfq_line in rfq_lines:
                    rfq_qty = rfq_line.product_uom_id._compute_quantity(rfq_line.product_qty, product_uom, round=False)
                    if product_uom.compare(quantity, rfq_qty) < 0:
                        quantity = 0
                    else:
                        quantity -= rfq_qty
                if not product_uom.is_zero(quantity):
                    # the missing quantity is reported in the unit of the reception note line
                    missing_qty = product_uom._compute_quantity(
                        quantity, line.product_uom_id, rounding_method="HALF-UP"
                    )
                    if not self.ignore_quantities:
                        quantity_errors.append(
                            self.env._(
                                "The quantity %(quantity)s of the [%(default_code)s] %(name)s product is not found "
                                "in a sent RFQ. Tick 'Ignore quantities' to receive it anyway.",
                                quantity=missing_qty,
                                default_code=line.product_id.default_code,
                                name=line.product_id.name,
                            )
                        )

                    else:
                        vals = {
                            "product_id": line.product_id,
                            "product_qty": missing_qty,
                            "uom": line.product_uom_id,
                        }
                        lines_to_add.append(vals)
                if not quantity_errors:
                    quantity = line_qty
                    for rfq_line in rfq_lines:
                        rfq_qty = rfq_line.product_uom_id._compute_quantity(
                            rfq_line.product_qty, product_uom, round=False
                        )
                        if not product_uom.compare(quantity, 0.0) > 0:
                            break
                        if product_uom.compare(quantity, rfq_qty) < 0:
                            product_qty = product_uom._compute_quantity(
                                rfq_qty - quantity, rfq_line.product_uom_id, round=False
                            )
                            quantity = 0
                        else:
                            quantity -= rfq_qty
                            product_qty = 0.0
                        # se retine consumul, in unitatea liniei RFQ (dupa rotunjirea campului), ca anularea
                        # notei sa poata restitui exact ce s-a scazut
                        previous_qty = rfq_line.product_qty
                        rfq_line.write({"product_qty": product_qty})
                        consumption_vals.append(
                            {
                                "note_id": self.id,
                                "rfq_line_id": rfq_line.id,
                                "quantity": previous_qty - rfq_line.product_qty,
                            }
                        )
                rfq_lines.order_id.check_if_empty()
        errors = found_errors + quantity_errors
        if errors:
            raise UserError("\n".join(errors))
        self.env["purchase.reception.note.consumption"].create(consumption_vals)
        return lines_to_add

    def check_if_empty(self):
        for order in self:
            qty = 0.0
            for line in order.order_line:
                qty += line.product_qty
            if qty == 0.0:
                order.write({"is_empty": True})


class PurchaseReceptionNoteConsumption(models.Model):
    _name = "purchase.reception.note.consumption"
    _description = "Quantity consumed from an RFQ line by a reception note"

    note_id = fields.Many2one("purchase.order", string="Reception note", required=True, ondelete="cascade", index=True)
    rfq_line_id = fields.Many2one("purchase.order.line", string="RFQ line", required=True, ondelete="cascade")
    quantity = fields.Float(
        string="Quantity",
        digits="Product Unit",
        required=True,
        help="Quantity taken from the RFQ line, in the unit of measure of the RFQ line",
    )
