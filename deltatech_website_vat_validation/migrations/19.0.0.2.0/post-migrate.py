# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The Romanian checks of the tax code moved to l10n_ro_website_anaf (l10n-romania).

    A database that had them (l10n_ro_partner_create_by_vat installed: the ANAF look-up was active)
    keeps them: the new module is installed in the same update, when it is on the addons path.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Module = env["ir.module.module"]
    if not Module.search_count([("name", "=", "l10n_ro_partner_create_by_vat"), ("state", "=", "installed")]):
        return
    # the module may be new on the addons path: register it first
    Module.update_list()
    target = Module.search([("name", "=", "l10n_ro_website_anaf")])
    if not target:
        _logger.warning(
            "The ANAF check of the tax code moved to l10n_ro_website_anaf, which is not on the addons "
            "path: add l10n-romania and install it to keep the check."
        )
    elif target.state == "uninstalled":
        target.button_install()
        _logger.info("The ANAF check of the tax code moved to l10n_ro_website_anaf: installed with this update.")
