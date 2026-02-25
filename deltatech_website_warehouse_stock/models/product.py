# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_warehouse_stock_distribution(self):
        warehouses = self.env["stock.warehouse"].search([("website_stock_display", "=", True)])
        threshold = int(
            self.env["ir.config_parameter"].sudo().get_param("deltatech_website_warehouse_stock.threshold", 10)
        )
        warehouse_stock_lines = []
        for warehouse in warehouses:
            if warehouse.lot_stock_id.usage == "internal":
                qty = self.with_context(location=warehouse.lot_stock_id.id)._compute_quantities_dict()
                quantity_in_warehouse = qty[self.id]["qty_available"] - qty[self.id]["outgoing_qty"]
                if quantity_in_warehouse > threshold:
                    warehouse_stock_lines.append(
                        {
                            "warehouse": warehouse.name,
                            "quantity": _("Available"),
                            "badge": "green",
                        }
                    )
                elif quantity_in_warehouse > 0:
                    warehouse_stock_lines.append(
                        {
                            "warehouse": warehouse.name,
                            "quantity": quantity_in_warehouse,
                            "badge": "grey",
                        }
                    )
                else:
                    warehouse_stock_lines.append(
                        {
                            "warehouse": warehouse.name,
                            "quantity": _("Out of stock"),
                            "badge": "red",
                        }
                    )
        return warehouse_stock_lines
