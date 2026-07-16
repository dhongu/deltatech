from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    check_min_website = fields.Boolean(
        string="Website Check Quantity",
        default=True,
        help="Apply minimum and multiple quantity rules only on the website.",
    )

    def _get_additionnal_combination_info(
        self,
        product_or_template,
        quantity,
        uom,
        date,
        website,
    ) -> dict:
        combination_info = super()._get_additionnal_combination_info(
            product_or_template,
            quantity,
            uom,
            date,
            website,
        )
        product = (
            product_or_template
            if product_or_template._name == "product.product"
            else product_or_template.product_variant_id
            if product_or_template.product_variant_count == 1
            else self.env["product.product"]
        )
        website_product = product.with_context(website_id=website.id) if product else product
        minimum, multiple = website_product._get_sale_quantity_rules(uom) if product else (0.0, 0.0)
        combination_info.update(
            {
                "sale_qty_minimum": minimum,
                "sale_qty_multiple": multiple,
                "sale_qty_precision": self.env["decimal.precision"].precision_get("Product Unit"),
            }
        )
        return combination_info


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _should_enforce_sale_quantity_rules(self) -> bool:
        self.ensure_one()
        if self.check_min_website and not self.env.context.get("website_id"):
            return False
        return super()._should_enforce_sale_quantity_rules()
