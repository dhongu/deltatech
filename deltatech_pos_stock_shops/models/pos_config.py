from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    display_shop_stock = fields.Boolean(
        string="Display Stock in Other Shops",
        help="Show, next to the stock of this shop, how much the other shops have. The figures "
        "are loaded with the session, so the register still shows them when the network is down.",
    )
    stock_shop_warehouse_ids = fields.Many2many(
        "stock.warehouse",
        "pos_config_stock_shop_warehouse_rel",
        "config_id",
        "warehouse_id",
        string="Other Shops",
        domain="[('company_id', '=', company_id)]",
        help="Warehouses shown as other shops. Left empty, the warehouses of the other points of "
        "sale of the company are used, so the central warehouse or a transit location only shows "
        "up when chosen here.",
    )
    # Loaded with pos.config (which reads every field): the register needs the shop names
    # without stock.warehouse being a POS model.
    stock_shop_list = fields.Json(compute="_compute_stock_shop_list")

    @api.depends(
        "display_stock",
        "display_shop_stock",
        "stock_shop_warehouse_ids",
        "picking_type_id.warehouse_id",
        "company_id",
    )
    def _compute_stock_shop_list(self):
        for config in self:
            config.stock_shop_list = [
                {"id": warehouse.id, "name": warehouse.name} for warehouse in config._get_stock_shop_warehouses()
            ]

    def _get_stock_shop_warehouses(self):
        """The warehouses shown as other shops, without the shop of this register.

        Read with sudo: it runs while the session of a cashier loads, and a cashier does not
        necessarily have access to picking types and warehouses.
        """
        self.ensure_one()
        config = self.sudo()
        warehouses = self.env["stock.warehouse"].sudo()
        if not (config.display_stock and config.display_shop_stock):
            return warehouses
        own_warehouse = config.picking_type_id.warehouse_id
        if config.stock_shop_warehouse_ids:
            warehouses = config.stock_shop_warehouse_ids
        else:
            warehouses = config.search(
                [("company_id", "=", config.company_id.id), ("id", "!=", config._origin.id)]
            ).picking_type_id.warehouse_id
        warehouses = warehouses.filtered(lambda w: w.company_id == config.company_id) - own_warehouse
        return warehouses.sorted(lambda w: (w.sequence, w.name))
