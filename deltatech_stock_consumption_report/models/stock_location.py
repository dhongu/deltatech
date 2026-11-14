from odoo import api, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    @api.model
    def _get_consumption_usages(self):
        """Tipurile de locatie ale bonurilor de consum. Implicit cele din localizarea romana
        (l10n_ro_stock_account), daca exista; alte module pot extinde lista."""
        usages = dict(self._fields["usage"]._description_selection(self.env))
        return [usage for usage in ("consume", "usage_giving") if usage in usages]
