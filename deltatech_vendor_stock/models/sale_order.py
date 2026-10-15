# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.tools.misc import formatLang


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vendor_qty_available = fields.Float(
        "Vendor Quantity Available",
        digits="Product Unit",
        compute="_compute_qty_at_date",
    )
    other_qty_available = fields.Float(
        "Other Quantity Available",
        digits="Product Unit",
        compute="_compute_qty_at_date",
    )

    warehouse_stock = fields.Text(string="Stock/WH", compute="_compute_warehouse_stocks")

    def _get_stock_colors(self):
        """Get stock colors from system parameters"""
        get_str = self.env["ir.config_parameter"].sudo().get_str
        return {
            "color_fulfilled": get_str("deltatech_vendor_stock.color_fulfilled", "#28a745"),
            "color_fulfilled_no_free_qty": get_str("deltatech_vendor_stock.color_fulfilled_no_free_qty", "#17a2b8"),
            "color_not_fulfilled": get_str("deltatech_vendor_stock.color_not_fulfilled", "#dc3545"),
            "color_vendor_available": get_str("deltatech_vendor_stock.color_vendor_available", "#ffc107"),
            "color_default": get_str("deltatech_vendor_stock.color_default", "#007bff"),
        }

    @api.model
    def get_stock_colors(self):
        """Get stock colors from system parameters - API method"""
        return self._get_stock_colors()

    @api.model
    def _vendor_stock_use_only_main_location(self):
        return self.env["ir.config_parameter"].sudo().get_bool("deltatech_vendor_stock.use_only_main_location")

    @api.model
    def _vendor_stock_free_qty_by_warehouse(self, products, warehouses):
        """{(product_id, warehouse_id): free_qty}, one batched read per warehouse"""
        only_main_location = self._vendor_stock_use_only_main_location()
        context = self.env.context
        result = {}
        for warehouse in warehouses:
            if only_main_location:
                scoped = products.with_context(location=warehouse.lot_stock_id.id)
            else:
                scoped = products.with_context(warehouse_id=warehouse.id)
            quantities = scoped._compute_quantities_dict(
                context.get("lot_id"),
                context.get("owner_id"),
                context.get("package_id"),
                context.get("from_date"),
                context.get("to_date"),
            )
            for product_id, values in quantities.items():
                result[(product_id, warehouse.id)] = values["free_qty"]
        return result

    @api.model
    def _vendor_stock_warehouses(self, company):
        return (
            self.env["stock.warehouse"]
            .search([("company_id", "=", company.id)])
            .filtered(lambda warehouse: warehouse.lot_stock_id.usage == "internal")
        )

    @api.model
    def get_warehouse_stock(self, product_id, uom_id=False, company_id=False, warehouse_id=False):
        """Free stock of a product in each warehouse of the company, for the availability popover.

        The warehouse of the order comes first and is listed even without stock; the other
        warehouses only when they have stock. Quantities are in the unit of measure of the line.
        """
        product = self.env["product.product"].browse(product_id).exists()
        if not product.is_storable:
            return []
        company = self.env["res.company"].browse(company_id) if company_id else self.env.company
        warehouses = self._vendor_stock_warehouses(company)
        if len(warehouses) <= 1:
            return []
        order_warehouse = warehouses.browse(warehouse_id) & warehouses
        line_uom = self.env["uom.uom"].browse(uom_id) if uom_id else product.uom_id
        free_qty = self._vendor_stock_free_qty_by_warehouse(product, warehouses)
        result = []
        for warehouse in order_warehouse | (warehouses - order_warehouse):
            quantity = free_qty.get((product.id, warehouse.id), 0.0)
            is_order_warehouse = warehouse == order_warehouse
            if product.uom_id.is_zero(quantity) and not is_order_warehouse:
                continue
            quantity = product.uom_id._compute_quantity(quantity, line_uom)
            result.append(
                {
                    "warehouse_id": warehouse.id,
                    "code": warehouse.code,
                    "name": warehouse.name,
                    "qty": line_uom.round(quantity),
                    "is_order_warehouse": is_order_warehouse,
                }
            )
        return result

    def _compute_warehouse_stocks(self):
        self.warehouse_stock = False
        lines = self.filtered(lambda line: line.product_id.is_storable and line.display_qty_widget)
        for company, company_lines in lines.grouped(lambda line: line.order_id.company_id or self.env.company).items():
            warehouses = self._vendor_stock_warehouses(company)
            if len(warehouses) <= 1:
                continue
            free_qty = self._vendor_stock_free_qty_by_warehouse(company_lines.product_id, warehouses)
            for sale_line in company_lines:
                product = sale_line.product_id
                line_uom = sale_line.product_uom_id or product.uom_id
                warehouse_stock_lines = []
                for warehouse in warehouses:
                    quantity = free_qty.get((product.id, warehouse.id), 0.0)
                    if product.uom_id.is_zero(quantity):
                        continue
                    quantity = product.uom_id._compute_quantity(quantity, line_uom)
                    quantity_text = formatLang(self.env, quantity, dp="Product Unit")
                    warehouse_stock_lines.append(f"{warehouse.code}: {quantity_text} {line_uom.name}")
                sale_line.warehouse_stock = " \t\n".join(warehouse_stock_lines)

    @api.onchange("product_id")
    def _onchange_product_recalculate_stock(self):
        self._compute_warehouse_stocks()

    def _compute_qty_at_date(self):
        res = super()._compute_qty_at_date()
        self.other_qty_available = 0
        for line in self:
            product = line.product_id
            quantity = product.vendor_qty_available
            if quantity and line.product_uom_id and line.product_uom_id != product.uom_id:
                quantity = product.uom_id._compute_quantity(quantity, line.product_uom_id)
            line.vendor_qty_available = quantity
        return res
