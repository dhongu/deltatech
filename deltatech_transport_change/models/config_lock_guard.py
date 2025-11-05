# © 2025 Deltatech / Terrabit
# Global guard to block create/write/unlink on selected configuration models in production

import logging
from functools import wraps

from odoo import models, tools
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)

_PARAM_LOCK_ENABLED = "deltatech_transport_change.config_lock_enabled"


class ConfigLockGuard(models.AbstractModel):
    _name = "config.lock.guard"
    _description = "Configuration Models Lock Guard"

    @tools.ormcache()
    def _protected_model_names(self):
        """Cached set of model technical names flagged as configuration models."""
        names = self.env["ir.model"].sudo().search([("is_config_model", "=", True)]).mapped("model")
        # Return an immutable for hashing across workers
        return frozenset(names)

    def _should_block(self, model_name):
        """Return True if ops on model_name should be blocked for current user.
        Conditions:
        - NOT neutralized (production): ir.config_parameter('database.is_neutralized') is False
        - Model is flagged on ir.model (is_config_model = True)
        - Current user is not superuser (and not bypass, if enabled later)
        Additionally, guard is disabled during module install/update to allow data loading.
        """
        try:
            # Fast-path exits
            if self.env.user._is_superuser():
                return False
            # Allow during module install/update and data loading
            ctx = self.env.context or {}
            if ctx.get("install_mode") or ctx.get("module") or ctx.get("loading_modules"):
                return False

            # If model is not marked as protected, skip
            if model_name not in self._protected_model_names():
                return False

            # Only block in production (non-neutralized)
            icp = self.env["ir.config_parameter"].sudo()
            neutral = icp.get_param("database.is_neutralized", default=False)
            if str2bool(str(neutral)):
                return False

            return True
        except Exception as e:  # Never break core ops if guard fails; just log and allow
            _logger.exception("[ConfigLock] Guard check failed: %s", e)
            return False

    def _register_hook(self):
        # Patch BaseModel methods once per registry load
        Base = models.BaseModel
        for method_name in ("create", "write", "unlink"):
            original = getattr(Base, method_name)
            # Prevent double wrapping
            if getattr(original, "_config_lock_wrapped", False):  # pragma: no cover
                continue
            wrapped = self._wrap_method(original)
            wrapped._config_lock_wrapped = True  # type: ignore[attr-defined]
            setattr(Base, method_name, wrapped)
        return super()._register_hook()

    def _wrap_method(self, original):
        @wraps(original)
        def wrapper(recordset, *args, **kwargs):
            if self._should_block(recordset._name):
                from odoo.exceptions import UserError

                raise UserError("This model is protected in production. Direct create/write/delete is not allowed.")
            return original(recordset, *args, **kwargs)

        return wrapper
