from odoo import models
from odoo.fields import Domain


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _get_gather_domain(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
        """Consumă cheia de context `exclude_location_ids`, pusă de `stock.move._action_assign`
        când tipul de operație are activ `avoid_root_location_on_reservation`.

        Excluderea e implementată aici, ca opțiunea să funcționeze doar cu dependențele declarate
        ale modulului. Dacă e instalat și `deltatech_stock_removal_priority`, care aplică aceeași
        condiție, domeniul o primește de două ori, fără alt efect.
        """
        domain = super()._get_gather_domain(product_id, location_id, lot_id, package_id, owner_id, strict)
        exclude_location_ids = self.env.context.get("exclude_location_ids")
        if exclude_location_ids:
            domain = Domain.AND([domain, Domain("location_id", "not in", exclude_location_ids)])
        return domain
