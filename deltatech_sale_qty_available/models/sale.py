# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ready = fields.Boolean(string="Is ready", compute="_compute_is_ready")

    # aceasta functie poate sa fie consumatoare de resurse !
    # trebuie sa scaneze stocurile pentru toate produsele din comenzile de vanzare afisate
    @api.multi
    def _compute_is_ready(self):
        for order in self:
            # daca comand este deja facturata ea nu poate sa mai fie si gata de livrare
            is_ready = order.state in ["sent", "sale", "done"] and order.invoice_status != "invoiced"
            if is_ready:
                for line in order.order_line:
                    is_ready = is_ready and (line.qty_available >= line.product_uom_qty)
            order.is_ready = is_ready


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_available = fields.Float(related="product_id.qty_available", string="Quantity On Hand")
    virtual_available = fields.Float(related="product_id.virtual_available", string="Forecast Quantity")
    qty_available_text = fields.Char(string="Available", compute="_compute_qty_available_text")

    qty_to_deliver = fields.Float(compute="_compute_qty_to_deliver")
    display_qty_widget = fields.Boolean(compute="_compute_qty_to_deliver")

    @api.depends("product_id", "product_uom_qty", "qty_delivered", "state")
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            if line.state in ["draft", "sent"] and line.product_id.type == "product" and line.qty_to_deliver > 0:
                line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    @api.multi
    @api.depends("product_id", "route_id")
    def _compute_qty_available_text(self):
        for line in self:
            product = line.product_id
            if line.route_id:
                location = False
                for pull in line.route_id.pull_ids:
                    location = pull.location_src_id
                if location:
                    product = line.product_id.with_context(location=location.id)
            qty_available_text = "N/A"

            qty_available, virtual_available = product.qty_available, product.virtual_available
            outgoing_qty, incoming_qty = product.outgoing_qty, product.incoming_qty

            if qty_available or virtual_available or outgoing_qty or incoming_qty:
                qty_available_text = "%s = " % virtual_available
                if qty_available:
                    qty_available_text += " %s " % qty_available
                if outgoing_qty:
                    qty_available_text += " -%s " % outgoing_qty
                if incoming_qty:
                    qty_available_text += " +%s " % incoming_qty

            line.qty_available_text = qty_available_text
