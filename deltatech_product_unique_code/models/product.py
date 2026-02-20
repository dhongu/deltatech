from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import format_list


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("default_code", "barcode", "active")
    def _check_unique_code(self):
        self.env["product.product"].with_context(active_test=False)._check_unique_code_all(self.product_variant_ids)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("default_code", "barcode", "active")
    def _check_unique_code(self):
        self._check_unique_code_all(self)

    def _check_unique_code_all(self, products):
        self._check_unique_field_all(products, "default_code", _("Internal Reference"))
        self._check_unique_field_all(products, "barcode", _("Barcode"))

    def _check_unique_field_all(self, products, field_name, label):
        if self.env.user.has_group("deltatech_product_unique_code.group_product_duplicate_code"):
            return
        values = products.mapped(field_name)
        values = [v for v in values if v]
        if not values:
            return

        # We check both product.product and product.template because codes can be in either
        # (though usually they are synced, in some configurations they might not be)
        # and we want to prevent duplicates across both.

        for model_name in ["product.product", "product.template"]:
            domain = [(field_name, "in", values)]
            # Search for all products/templates with these codes, including archived ones
            all_records = self.env[model_name].sudo().with_context(active_test=False).search(domain)

            # Map values to records for error message
            duplicates = {}
            for record in all_records:
                val = record[field_name]
                if val not in duplicates:
                    duplicates[val] = self.env[model_name]
                duplicates[val] += record

            error_msgs = []
            for val, records in duplicates.items():
                # Filter out the records being currently validated
                if model_name == "product.product":
                    other_records = records - products
                else:
                    # For template, we need to check if the templates belong to the products being validated
                    other_records = records - products.product_tmpl_id

                if other_records:
                    error_msgs.append(
                        _(
                            "- %(label)s '%(val)s' already assigned to: %(records)s",
                            label=label,
                            val=val,
                            records=format_list(self.env, other_records.mapped("display_name")),
                        )
                    )

            if error_msgs:
                raise ValidationError(
                    _(
                        "The %(label)s must be unique (including archived products):\n%(msgs)s",
                        label=label,
                        msgs="\n".join(error_msgs),
                    )
                )
