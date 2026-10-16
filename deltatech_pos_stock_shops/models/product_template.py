from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import float_is_zero, float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # {"<warehouse id>": quantity}, only for the shops that have something. Filled only when
    # the POS asks for it (see `_load_pos_data_read`); everywhere else it stays empty.
    pos_shop_stock = fields.Json(
        string="Stock in Other Shops",
        compute="_compute_pos_shop_stock",
        compute_sudo=False,
    )

    @api.depends_context("pos_shop_warehouse_ids", "pos_shop_free_qty")
    def _compute_pos_shop_stock(self):
        warehouse_ids = self.env.context.get("pos_shop_warehouse_ids")
        stock = {}
        if warehouse_ids and self._origin:
            stock = self._origin._get_pos_shop_stock(warehouse_ids, self.env.context.get("pos_shop_free_qty"))
        for template in self:
            template.pos_shop_stock = stock.get(template._origin.id, {})

    def _get_pos_shop_stock(self, warehouse_ids, free_qty=False):
        """Quantity per template and warehouse, in one grouped read over the quants.

        Reading `qty_available` with a `warehouse_id` context would cost one query per shop.
        The other shops are read with sudo: a cashier may not have access to the stock of
        another warehouse, but knowing how much is there is the whole point. The warehouses
        come from the POS configuration, already limited to its company.
        """
        warehouses = self.env["stock.warehouse"].sudo().browse(warehouse_ids).exists()
        variants = self.product_variant_ids
        if not warehouses or not variants:
            return {}
        groups = (
            self.env["stock.quant"]
            .sudo()
            ._read_group(
                [
                    ("product_id", "in", variants.ids),
                    ("location_id", "child_of", warehouses.view_location_id.ids),
                    ("location_id.usage", "=", "internal"),
                ],
                ["product_id", "location_id"],
                ["quantity:sum", "reserved_quantity:sum"],
            )
        )
        quantities = defaultdict(lambda: defaultdict(float))
        for product, location, quantity, reserved in groups:
            warehouse = location.warehouse_id
            if warehouse not in warehouses:
                continue
            value = quantity - reserved if free_qty else quantity
            quantities[product.product_tmpl_id.id][warehouse.id] += value
        result = {}
        for template in self.filtered(lambda t: t.id in quantities):
            rounding = template.uom_id.rounding
            per_shop = {
                str(warehouse_id): float_round(qty, precision_rounding=rounding)
                for warehouse_id, qty in quantities[template.id].items()
                if not float_is_zero(qty, precision_rounding=rounding)
            }
            if per_shop:
                result[template.id] = per_shop
        return result

    @api.model
    def _load_pos_data_fields(self, config):
        result = super()._load_pos_data_fields(config)
        if config._get_stock_shop_warehouses() and "pos_shop_stock" not in result:
            result = result + ["pos_shop_stock"]
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        # Also the path of `_notify_pos_stock_change` (deltatech_pos_stock): a sale in one shop
        # pushes the fresh figures to the registers of the other shops as well.
        warehouses = config._get_stock_shop_warehouses()
        if warehouses:
            records = records.with_context(
                pos_shop_warehouse_ids=warehouses.ids,
                pos_shop_free_qty=config.stock_badge_quantity == "available",
            )
        return super()._load_pos_data_read(records, config)
