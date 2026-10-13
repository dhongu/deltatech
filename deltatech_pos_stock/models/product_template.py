from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # `product.product` carries free_qty, `product.template` does not: core aggregates
    # qty_available and the forecast onto the template but stops short of the free
    # quantity. The POS card is handed a template, so the badge needs it here.
    free_qty = fields.Float(
        "Free To Use Quantity",
        compute="_compute_free_qty",
        compute_sudo=False,
        digits="Product Unit",
    )

    def _compute_free_qty(self):
        variants = self.product_variant_ids._origin
        per_variant = {p["id"]: p["free_qty"] for p in variants.read(["free_qty"])} if variants else {}
        for template in self:
            template.free_qty = sum(
                per_variant.get(variant.id, 0.0) for variant in template.product_variant_ids._origin
            )

    @api.model
    def _load_pos_data_fields(self, config):
        # În 19.0 cardul de produs din POS primește un `product.template`,
        # așa că stocul trebuie încărcat pe șablon, nu pe variantă.
        result = super()._load_pos_data_fields(config)
        if config.display_stock:
            if "qty_available" not in result:
                result = result + ["qty_available"]
            # Only paid for when the badge actually shows it: free_qty means reading every
            # variant's reservations, and configs left on "on hand" should not carry that.
            if config.stock_badge_quantity == "available" and "free_qty" not in result:
                result = result + ["free_qty"]
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        if config.display_stock and config.warehouse_id:
            records = records.with_context(warehouse_id=config.warehouse_id.id)
        return super()._load_pos_data_read(records, config)

    def _notify_pos_stock_change(self, only_available_badges=False):
        # `qty_available` e un câmp calculat, nestocat: o vânzare scrie pe stock.quant,
        # nu pe product.template, deci write_date-ul șablonului nu se schimbă niciodată
        # și sincronizarea normală a POS-ului (bazată pe write_date, vezi pos.load.mixin)
        # nu retrimite niciodată stocul actualizat către sesiunile deja deschise. Împingem
        # explicit valoarea proaspătă pe bus-ul folosit deja de core pentru sincronizarea
        # între dispozitive (`notify_synchronisation`).
        #
        # `only_available_badges` restricts the push to the registers whose badge shows the
        # available quantity. Reservations move far more often than physical stock, so the
        # registers showing stock on hand must not be woken up for every single sale.
        if not self:
            return
        domain = [("state", "=", "opened"), ("config_id.display_stock", "=", True)]
        if only_available_badges:
            domain.append(("config_id.stock_badge_quantity", "=", "available"))
        company_ids = self.mapped("company_id").ids
        if company_ids:
            domain.append(("company_id", "in", company_ids))
        sessions = self.env["pos.session"].sudo().search(domain)
        for config in sessions.config_id:
            data = self._load_pos_data_read(self, config)
            if data:
                config._notify("STOCK_SYNCHRONISATION", {"product.template": data})
