from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import format_list

CODE_FIELDS = ["default_code", "barcode"]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        variants = templates.with_context(active_test=False).product_variant_ids
        self.env["product.product"]._check_unique_code_all(variants)
        return templates

    def write(self, vals):
        fields_to_check = [f for f in CODE_FIELDS if f in vals]
        if not fields_to_check:
            return super().write(vals)
        variants = self.with_context(active_test=False).product_variant_ids
        old_values = {f: {p.id: p[f] or "" for p in variants} for f in fields_to_check}
        res = super().write(vals)
        # the check runs after super() so the template inverse fields have already
        # propagated to the variants; only values that actually changed are validated,
        # so pre-existing duplicates do not block unrelated fixes on the same record
        variants = self.with_context(active_test=False).product_variant_ids
        product_model = self.env["product.product"]
        for field_name in fields_to_check:
            changed = variants.filtered(lambda p, f=field_name: (p[f] or "") != old_values[f].get(p.id, ""))
            product_model._check_unique_field_all(changed, field_name)
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        self._check_unique_code_all(products)
        return products

    def write(self, vals):
        fields_to_check = [f for f in CODE_FIELDS if f in vals]
        if not fields_to_check:
            return super().write(vals)
        old_values = {f: {p.id: p[f] or "" for p in self} for f in fields_to_check}
        res = super().write(vals)
        for field_name in fields_to_check:
            changed = self.filtered(lambda p, f=field_name: (p[f] or "") != old_values[f].get(p.id, ""))
            self._check_unique_field_all(changed, field_name)
        return res

    def _check_unique_code_all(self, products):
        for field_name in CODE_FIELDS:
            self._check_unique_field_all(products, field_name)

    @api.model
    def _unique_code_field_label(self, field_name):
        return _("Internal Reference") if field_name == "default_code" else _("Barcode")

    def _check_unique_field_all(self, products, field_name):
        if self.env.user.has_group("deltatech_product_unique_code.group_product_duplicate_code"):
            return
        values = products.mapped(field_name)
        values = [v for v in values if v]
        if not values:
            return
        label = self._unique_code_field_label(field_name)

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
