# ©  2024 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.osv.expression import AND


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        # The generic search-panel "category" range (select="one") only accepts
        # many2one/selection fields. `public_categ_ids` (website categories) is a
        # many2many, but every helper used below already supports many2many
        # (see _search_panel_domain_image), so we reproduce the standard
        # hierarchical algorithm for it instead of hitting the type guard.
        if field_name != "public_categ_ids":
            return super().search_panel_select_range(field_name, **kwargs)

        comodel = self.env["product.public.category"].with_context(hierarchical_naming=False)
        parent_name = comodel._parent_name  # 'parent_id'
        field_names = ["display_name", parent_name]

        def get_parent_id(record):
            value = record[parent_name]
            return value and value[0]

        model_domain = kwargs.get("search_domain", [])
        extra_domain = AND(
            [
                kwargs.get("category_domain", []),
                kwargs.get("filter_domain", []),
            ]
        )
        comodel_domain = kwargs.get("comodel_domain", [])
        enable_counters = kwargs.get("enable_counters")
        expand = kwargs.get("expand")
        limit = kwargs.get("limit")

        if enable_counters or not expand:
            domain_image = self._search_panel_field_image(
                field_name,
                model_domain=model_domain,
                extra_domain=extra_domain,
                only_counters=expand,
                set_limit=False,
                **kwargs,
            )

        if not expand:
            image_element_ids = list(domain_image.keys())
            comodel_domain = AND([comodel_domain, [("id", "parent_of", image_element_ids)]])

        comodel_records = comodel.search_read(comodel_domain, field_names, limit=limit)

        ids = [rec["id"] for rec in comodel_records] if expand else image_element_ids
        comodel_records = self._search_panel_sanitized_parent_hierarchy(comodel_records, parent_name, ids)

        field_range = {}
        for record in comodel_records:
            record_id = record["id"]
            values = {
                "id": record_id,
                "display_name": record["display_name"],
                parent_name: get_parent_id(record),
            }
            if enable_counters:
                image_element = domain_image.get(record_id)
                values["__count"] = image_element["__count"] if image_element else 0
            field_range[record_id] = values

        if enable_counters:
            self._search_panel_global_counters(field_range, parent_name)

        return {
            "parent_field": parent_name,
            "values": list(field_range.values()),
        }
