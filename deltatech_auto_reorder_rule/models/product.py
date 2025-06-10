# ©  2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def create_rule(self):
        warehouses = self.env["stock.warehouse"].search(
            [("generate_reorder_rules", "=", True), ("company_id", "=", self.env.user.company_id.id)]
        )
        routes = self.env["stock.route"].search(
            [
                ("use_this_for_auto_rules", "=", True),
            ]
        )
        route = False
        if routes:
            route = routes[0].id
        for record in self:
            rules = record.env["stock.warehouse.orderpoint"].search(
                [("product_id", "=", record.id), ("company_id", "=", self.env.user.company_id.id)]
            )
            if not rules:
                values = []
                for warehouse in warehouses:
                    if warehouse.lot_stock_id.usage == "internal":
                        use_auto_rules = (
                            self.env["ir.config_parameter"]
                            .sudo()
                            .get_param("deltatech_auto_reorder_rule.use_auto_instead_of_manual_rules", default=False)
                        )
                        values.append(
                            {
                                "product_id": record.id,
                                "product_min_qty": 0,
                                "product_max_qty": 0,
                                "qty_multiple": 0,
                                "trigger": "manual" if not use_auto_rules else "auto",
                                "route_id": route,
                                "location_id": warehouse.lot_stock_id.id,
                            }
                        )
                if values:
                    record.env["stock.warehouse.orderpoint"].create(values)

            # if not rules and record.type == "product":
            #     record.env["stock.warehouse.orderpoint"].create(
            #         {
            #             "product_id": record.id,
            #             "product_min_qty": 0,
            #             "product_max_qty": 0,
            #             "qty_multiple": 0,
            #         }
            #     )

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        dont_auto_create_rule = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("deltatech_auto_reorder_rule.dont_auto_create_rule", default=False)
        )
        if not dont_auto_create_rule:
            products.create_rule()
        return products
