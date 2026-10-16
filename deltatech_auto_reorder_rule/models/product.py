# ©  2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.tools import str2bool


class ProductProduct(models.Model):
    _inherit = "product.product"

    def create_rule(self):
        # The rules are generated for the company of the product or, for products shared between companies,
        # for the active company (env.company), not for the default company of the user.
        for record in self:
            company = record.company_id or self.env.company
            warehouses = self.env["stock.warehouse"].search(
                [("generate_reorder_rules", "=", True), ("company_id", "=", company.id)]
            )
            routes = self.env["stock.route"].search(
                [
                    ("use_this_for_auto_rules", "=", True),
                    ("company_id", "in", [company.id, False]),
                ]
            )
            route = False
            if routes:
                route = routes[0].id
            orderpoint_model = record.env["stock.warehouse.orderpoint"].with_company(company)
            # an existing rule only covers its own location: the other warehouses still get theirs
            rules = orderpoint_model.with_context(active_test=False).search(
                [("product_id", "=", record.id), ("company_id", "=", company.id)]
            )
            values = []
            for warehouse in warehouses:
                location = warehouse.lot_stock_id
                if location.usage == "internal" and location not in rules.location_id:
                    values.append(
                        {
                            "product_id": record.id,
                            "product_min_qty": 0,
                            "product_max_qty": 0,
                            "trigger": "manual",
                            "route_id": route,
                            "location_id": location.id,
                            "company_id": company.id,
                        }
                    )
            if values:
                orderpoint_model.create(values)

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
            .get_param("deltatech_auto_reorder_rule.dont_auto_create_rule", default="False")
        )
        if not str2bool(dont_auto_create_rule or "False", default=False):
            products.create_rule()
        return products
