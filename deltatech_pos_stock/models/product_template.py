from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # free_qty (stock minus reservations) is defined on product.template by core since 20.0,
    # computed with the other quantities in `_compute_quantities`.

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
        # A shared product (no company) is sold by the registers of every company, so the
        # sessions are restricted by company only when every product in the batch has one.
        if all(template.company_id for template in self):
            domain.append(("company_id", "in", self.company_id.ids))
        sessions = self.env["pos.session"].sudo().search(domain)
        for config in sessions.config_id:
            templates = self.filtered(lambda t, c=config.company_id: not t.company_id or t.company_id == c)
            if not templates:
                continue
            data = self._load_pos_data_read(templates, config)
            if data:
                config._notify("STOCK_SYNCHRONISATION", {"product.template": data})
