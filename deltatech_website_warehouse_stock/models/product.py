# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools import float_repr, float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_warehouse_stock_distribution(self):
        """One line per warehouse shown on the website:

        - ``warehouse``: name of the warehouse;
        - ``quantity``: quantity or text shown (``Available``, ``In stock``, ``Out of stock``,
          ``On order``);
        - ``badge``: ``green`` above the threshold, ``grey`` between 1 and the threshold,
          ``red`` at zero;
        - ``state``: ``in_stock`` or ``on_order`` (zero stock with the 'On order' message),
          ``out`` otherwise at zero;
        - ``qty``: available quantity, for the warehouse selector;
        - ``message``: sentence of the warehouse selector.
        """
        self.ensure_one()
        # Called with sudo() from the public product page: company rules do not apply,
        # so the warehouses are restricted explicitly to the current website's company.
        # env.website is empty outside a website request: fall back to the current company.
        website = self.env.website
        company = website.company_id or self.env.company
        warehouses = self.env["stock.warehouse"].search(
            [("website_stock_display", "=", True), ("company_id", "=", company.id)]
        )
        threshold = self.env["ir.config_parameter"].sudo().get_int("deltatech_website_warehouse_stock.threshold", 10)
        status_only = website.warehouse_stock_qty_display == "status_only"
        on_order = website.warehouse_stock_zero_message == "on_order"
        warehouse_stock_lines = []
        for warehouse in warehouses:
            if warehouse.lot_stock_id.usage == "internal":
                qty = self.with_context(location=warehouse.lot_stock_id.id)._compute_quantities_dict()
                quantity_in_warehouse = qty[self.id]["qty_available"] - qty[self.id]["outgoing_qty"]
                line = {"warehouse": warehouse.name, "qty": max(quantity_in_warehouse, 0)}
                if quantity_in_warehouse > threshold:
                    line.update(
                        quantity=self.env._("In stock") if status_only else self.env._("Available"),
                        badge="green",
                        state="in_stock",
                    )
                elif quantity_in_warehouse > 0:
                    line.update(
                        quantity=self.env._("In stock")
                        if status_only
                        else self._warehouse_stock_qty_text(quantity_in_warehouse),
                        badge="grey",
                        state="in_stock",
                    )
                else:
                    line.update(
                        quantity=self.env._("On order") if on_order else self.env._("Out of stock"),
                        badge="red",
                        state="on_order" if on_order else "out",
                    )
                line["message"] = self._warehouse_stock_message(line, status_only)
                warehouse_stock_lines.append(line)
        return warehouse_stock_lines

    def _warehouse_stock_message(self, line, status_only):
        if line["state"] == "in_stock":
            if status_only:
                return self.env._("In stock at %(warehouse)s. Ready for delivery.", warehouse=line["warehouse"])
            return self.env._(
                "In stock at %(warehouse)s: %(qty)s pcs. Ready for delivery.",
                warehouse=line["warehouse"],
                qty=self._warehouse_stock_qty_text(line["qty"]),
            )
        if line["state"] == "on_order":
            return self.env._(
                "Currently not on the shelf at %(warehouse)s. Brought in on order.", warehouse=line["warehouse"]
            )
        return self.env._("Out of stock at %(warehouse)s.", warehouse=line["warehouse"])

    def _warehouse_stock_qty_text(self, qty):
        # 3 instead of 3.0, 2.5 kept as it is
        qty = float_round(qty, precision_digits=3)
        return str(int(qty)) if qty == int(qty) else float_repr(qty, 3).rstrip("0")
