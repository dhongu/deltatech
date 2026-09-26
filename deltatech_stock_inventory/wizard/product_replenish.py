# ©  2024 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    reference_id = fields.Many2one("stock.reference", string="Grupare")

    @api.onchange("warehouse_id")
    def _onchange_warehouse_id_reference(self):
        for wizard in self:
            wizard.reference_id = wizard.warehouse_id and wizard._get_daily_reference(wizard.warehouse_id)

    def _get_daily_reference(self, warehouse):
        # Toate reaprovizionările manuale lansate în aceeași zi, din același
        # depozit, primesc aceeași referință, ca să ajungă pe un singur
        # stock.picking în loc de câte unul per produs (comportamentul
        # câmpului "Grupare" din 18.0, portat pe stock.reference).
        name = self.env._(
            "Reaprovizionare %(warehouse)s %(date)s",
            warehouse=warehouse.code or warehouse.name,
            date=fields.Date.context_today(self),
        )
        StockReference = self.env["stock.reference"]
        reference = StockReference.search([("name", "=", name)], limit=1)
        if not reference:
            reference = StockReference.create({"name": name})
        return reference

    def _prepare_run_values(self):
        # OVERRIDE
        values = super()._prepare_run_values()
        if not self.reference_id and self.warehouse_id:
            # Formularul completează câmpul la schimbarea depozitului (onchange), dar un
            # apel programatic (fără trecere prin UI) poate crea wizard-ul fără să declanșeze
            # onchange-urile, deci recalculăm aici ca ultimă plasă de siguranță.
            self.reference_id = self._get_daily_reference(self.warehouse_id)
        if not self.reference_id:
            return values

        domain = [
            ("reference_ids", "in", self.reference_id.ids),
            ("product_id", "=", self.product_id.id),
            ("state", "=", "done"),
        ]
        if self.env["stock.move"].search(domain, limit=1):
            raise UserError(self.env._("Reaprovizionarea a fost deja făcută astăzi pentru acest produs și depozit."))

        values["reference_ids"] = self.reference_id
        return values
