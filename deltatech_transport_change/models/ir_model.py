# © 2025 Deltatech / Terrabit
# Extend ir.model to mark configuration models

from odoo import fields, models


class IrModel(models.Model):
    _inherit = "ir.model"

    is_config_model = fields.Boolean(
        string="Configuration Model",
        help=(
            "If enabled, this model is considered a configuration model. "
            "When the database is NOT neutralized (production), direct create/write/delete "
            "operations can be blocked by deltatech_transport_change according to the guard rules."
        ),
    )

    def _clear_guard_cache(self):
        # Clear the ormcache for protected model names
        try:
            self.env["config.lock.guard"]._protected_model_names.clear_cache(self.env["config.lock.guard"])
        except Exception:
            # Best effort; do not block admin actions
            pass

    def write(self, vals):
        res = super().write(vals)
        if "is_config_model" in vals:
            self._clear_guard_cache()
        return res

    def create(self, vals_list):
        records = super().create(vals_list)
        # New models might be flagged as configuration
        if isinstance(vals_list, dict):
            vals_iter = [vals_list]
        else:
            vals_iter = vals_list
        if any("is_config_model" in v for v in vals_iter):
            self._clear_guard_cache()
        return records

    def unlink(self):
        res = super().unlink()
        # Model set changed; clear cache
        self._clear_guard_cache()
        return res
