from odoo import fields, models


class OrderRulesDetailsWizard(models.TransientModel):
    _name = "order.rules.details.wizard"
    _description = "Order Rules Details Wizard"

    min_quantity = fields.Float(string="Minimum Quantity", required=True)
    max_quantity = fields.Float(string="Maximum Quantity", required=True)
    stock_location_ids = fields.Many2many(
        comodel_name="stock.location", string="Stock Locations", help="Select stock locations for the order rules."
    )
    trigger = fields.Selection(
        [("auto", "Automatic"), ("manual", "Manual")], string="Trigger", required=True, default="manual"
    )

    def do_create(self):
        product_template = self.env["product.template"].browse(self.env.context.get("active_id"))
        orderpoint_model = self.env["stock.warehouse.orderpoint"]
        # each rule belongs to the company of its location (locations without company: the active company)
        locations_by_company = {}
        for location in self.stock_location_ids:
            company = location.company_id or self.env.company
            locations_by_company[company] = locations_by_company.get(company, location.browse()) | location
        for company, locations in locations_by_company.items():
            route = self.env["stock.route"].search(
                [("use_this_for_auto_rules", "=", True), ("company_id", "in", [company.id, False])], limit=1
            )
            values = []
            for variant in product_template.product_variant_ids:
                for location in locations:
                    values.append(
                        {
                            "product_id": variant.id,
                            "product_min_qty": self.min_quantity,
                            "product_max_qty": self.max_quantity,
                            "route_id": route.id,
                            "trigger": self.trigger,
                            "location_id": location.id,
                            "company_id": company.id,
                        }
                    )
            if values:
                orderpoint_model.with_company(company).create(values)
