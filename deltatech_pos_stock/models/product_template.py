from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _load_pos_data_fields(self, config):
        # În 19.0 cardul de produs din POS primește un `product.template`,
        # așa că stocul trebuie încărcat pe șablon, nu pe variantă.
        result = super()._load_pos_data_fields(config)
        if config.display_stock and "qty_available" not in result:
            result = result + ["qty_available"]
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        if config.display_stock and config.warehouse_id:
            records = records.with_context(warehouse_id=config.warehouse_id.id)
        return super()._load_pos_data_read(records, config)

    def _notify_pos_stock_change(self):
        # `qty_available` e un câmp calculat, nestocat: o vânzare scrie pe stock.quant,
        # nu pe product.template, deci write_date-ul șablonului nu se schimbă niciodată
        # și sincronizarea normală a POS-ului (bazată pe write_date, vezi pos.load.mixin)
        # nu retrimite niciodată stocul actualizat către sesiunile deja deschise. Împingem
        # explicit valoarea proaspătă pe bus-ul folosit deja de core pentru sincronizarea
        # între dispozitive (`notify_synchronisation`).
        if not self:
            return
        domain = [("state", "=", "opened"), ("config_id.display_stock", "=", True)]
        company_ids = self.mapped("company_id").ids
        if company_ids:
            domain.append(("company_id", "in", company_ids))
        sessions = self.env["pos.session"].sudo().search(domain)
        for config in sessions.config_id:
            data = self._load_pos_data_read(self, config)
            if data:
                config._notify("STOCK_SYNCHRONISATION", {"product.template": data})
