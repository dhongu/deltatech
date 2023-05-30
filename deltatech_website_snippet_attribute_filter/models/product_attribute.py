# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    def get_attribute_values(self, attribute_value_ids=None):
        self.ensure_one()

        values = self.env["product.attribute.value"]
        if not attribute_value_ids:
            domain = [("attribute_id", "=", self.id)]
            values |= self.env["product.attribute.value"].search(domain, order="name")
        else:
            if isinstance(attribute_value_ids, str):
                attribute_value_ids = [int(v) for v in attribute_value_ids.split(",")]
            domain = [("product_attribute_value_id", "in", attribute_value_ids)]
            template_values = self.env["product.template.attribute.value"].search(domain)
            domain = [
                ("product_tmpl_id", "in", template_values.mapped("product_tmpl_id").ids),
                ("attribute_id", "=", self.id),
            ]
            template_values = self.env["product.template.attribute.value"].search(domain)
            values |= template_values.mapped("product_attribute_value_id")

        return values.read(["id", "name"])
