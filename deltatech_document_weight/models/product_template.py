from odoo import api, fields, models

PROPAGATE_PARAM = "deltatech_document_weight.propagate_variants"
PROPAGATED_FIELDS = ("weight", "volume", "l10n_ro_net_weight")
NET_WEIGHT_XPATHS = [
    "//label[@for='l10n_ro_net_weight']",
    "//div[@name='l10n_ro_net_weight']",
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Same definition (and method names) as in l10n_ro_stock and l10n_ro_stock_base: whichever of them
    # is installed, it is the same field and the same column.
    l10n_ro_net_weight = fields.Float(
        "Net Weight",
        compute="_compute_l10n_ro_net_weight",
        inverse="_inverse_l10n_ro_net_weight",
        digits="Stock Weight",
        store=True,
    )
    l10n_ro_net_weight_uom_name = fields.Char(
        string="Net Weight unit of measure label",
        compute="_compute_l10n_ro_net_weight_uom_name",
    )

    def _compute_l10n_ro_net_weight_uom_name(self):
        self.l10n_ro_net_weight_uom_name = self._get_weight_uom_name_from_ir_config_parameter()

    @api.depends("product_variant_ids.l10n_ro_net_weight")
    def _compute_l10n_ro_net_weight(self):
        self._compute_template_field_from_variant_field("l10n_ro_net_weight")

    def _inverse_l10n_ro_net_weight(self):
        self._set_product_variant_field("l10n_ro_net_weight")

    def _get_related_fields_variant_template(self):
        return super()._get_related_fields_variant_template() + ["l10n_ro_net_weight"]

    @api.model
    def _document_weight_remove_duplicates(self, arch):
        """Keep a single net weight field on the form when other modules add it too."""
        for xpath in NET_WEIGHT_XPATHS:
            for node in arch.xpath(xpath)[1:]:
                node.getparent().remove(node)
        return arch

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            self._document_weight_remove_duplicates(arch)
        return arch, view

    @api.model
    def _document_weight_propagation_enabled(self):
        return self.env["ir.config_parameter"].sudo().get_bool(PROPAGATE_PARAM)

    def write(self, vals):
        res = super().write(vals)
        # Natively (Odoo 20) the weight and the volume reach all the variants, the net weight only those of a
        # template with a single variant. The value in ``vals`` is used, not the one read back: the template field is computed from the variants
        # and is 0 as soon as there are two or more.
        if self._document_weight_propagation_enabled():
            for fname in PROPAGATED_FIELDS:
                if fname in vals:
                    self.product_variant_ids.write({fname: vals[fname]})
        return res

    def _create_product_variant(self, combination, log_warning=False):
        # A variant created on demand (dynamic attributes, e.g. when the product is added to a
        # quotation line from the configurator) does not get these values from the template.
        # They are read BEFORE super(): the new variant has
        # 0 weight and volume, and the compute of the template field would reset them on the template.
        # The source is an existing variant if there is one: from the second variant on, the template
        # field is 0 (see ``_compute_template_field_from_variant_field``).
        if not self._document_weight_propagation_enabled():
            return super()._create_product_variant(combination, log_warning=log_warning)
        existing = self._get_variant_for_combination(combination)
        source = self.product_variant_ids[:1] or self
        pending_vals = {fname: source[fname] for fname in PROPAGATED_FIELDS}
        variant = super()._create_product_variant(combination, log_warning=log_warning)
        if variant and variant != existing:
            variant.write(pending_vals)
        return variant
