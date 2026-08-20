from odoo import models

PRICE_FIELDS = {"list_price", "standard_price"}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        # `list_price`/`standard_price` do bump the template's write_date, but a POS session
        # that is already open never re-runs the write_date-based sync (see
        # data_service.js loadInitialData()) — F5 just returns the cached IndexedDB data.
        # Push the fresh price explicitly, same bus pattern deltatech_pos_stock uses for stock.
        templates_to_notify = (
            self.filtered("available_in_pos") if PRICE_FIELDS & vals.keys() else self.env["product.template"]
        )
        res = super().write(vals)
        templates_to_notify._notify_pos_price_change()
        return res

    def _notify_pos_price_change(self):
        if not self:
            return
        domain = [("state", "=", "opened")]
        company_ids = self.mapped("company_id").ids
        if company_ids:
            domain.append(("company_id", "in", company_ids))
        sessions = self.env["pos.session"].sudo().search(domain)
        for config in sessions.config_id:
            data = self._load_pos_data_read(self, config)
            if data:
                config._notify("PRICE_SYNCHRONISATION", {"product.template": data})
