# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vendor_qty_available = fields.Float(
        "Vendor Quantity Available",
        digits="Product Unit of Measure",
        compute="_compute_qty_at_date",
    )
    other_qty_available = fields.Float(
        "Other Quantity Available",
        digits="Product Unit of Measure",
        compute="_compute_qty_at_date",
    )

    warehouse_stock = fields.Text(string="Stock/WH", compute="_compute_warehouse_stocks")

    def _compute_warehouse_stocks(self):
        warehouses = self.env["stock.warehouse"].search([])
        if len(warehouses) == 1:
            self.warehouse_stock = False
            return

        for sale_line in self:
            if sale_line.product_id:
                product = sale_line.product_id
                warehouse_stock_lines = []
                for warehouse in warehouses:
                    if warehouse.lot_stock_id.usage == "internal":
                        get_param = self.env["ir.config_parameter"].sudo().get_param
                        use_only_main_location = safe_eval(
                            get_param("deltatech_vendor_stock.use_only_main_location", "0")
                        )
                        if not use_only_main_location:
                            qty = product.with_context(warehouse=warehouse.id)._compute_quantities_dict(
                                self.env.context.get("lot_id"),
                                self.env.context.get("owner_id"),
                                self.env.context.get("package_id"),
                                self.env.context.get("from_date"),
                                self.env.context.get("to_date"),
                            )
                        else:
                            qty = product.with_context(location=warehouse.lot_stock_id.id)._compute_quantities_dict(
                                self.env.context.get("lot_id"),
                                self.env.context.get("owner_id"),
                                self.env.context.get("package_id"),
                                self.env.context.get("from_date"),
                                self.env.context.get("to_date"),
                            )

                        quantity_in_warehouse = qty[product.id]["qty_available"]
                        if quantity_in_warehouse:
                            line = f"{warehouse.code}: {quantity_in_warehouse}"
                            warehouse_stock_lines.append(line)
                sale_line.warehouse_stock = " \t\n".join(warehouse_stock_lines)
            else:
                sale_line.warehouse_stock = ""

    @api.onchange("product_id")
    def _onchange_product_recalculate_stock(self):
        self._compute_warehouse_stocks()

    def _compute_qty_at_date(self):
        res = super()._compute_qty_at_date()
        self.other_qty_available = 0
        treated = self.env["sale.order.line"]
        for line in self:
            line.vendor_qty_available = line.product_id.vendor_qty_available
            treated |= line
        remaining = self - treated
        remaining.vendor_qty_available = False
        return res
