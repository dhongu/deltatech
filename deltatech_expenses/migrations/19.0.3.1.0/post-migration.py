# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Înainte de această versiune, accesul la deltatech.expenses.deduction era acordat
    tuturor prin base.group_user (fără separare angajat/aprobator/contabil). Modulul introduce
    acum grupurile dedicate group_expenses_user/approver/accounting, cu acces restrâns per rol.

    Ca upgrade-ul să nu blocheze accesul utilizatorilor existenți, acordăm rolul cel mai permisiv
    (Contabil, care implică Aprobator și Angajat) tuturor userilor interni existenți — comportament
    identic cu ce aveau înainte. Administratorul trebuie să revizuiască ulterior și să reducă rolul
    userilor care nu ar trebui să aibă drept de validare/contabilizare (tichet POPVAL-COS, pct. 6)."""
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    accounting_group = env.ref("deltatech_expenses.group_expenses_accounting", raise_if_not_found=False)
    internal_group = env.ref("base.group_user", raise_if_not_found=False)
    if not accounting_group or not internal_group:
        return

    internal_users = env["res.users"].search([("group_ids", "in", internal_group.id)])
    internal_users.write({"group_ids": [(4, accounting_group.id)]})
    _logger.info(
        "deltatech_expenses: acordat rolul Contabil (compatibilitate upgrade) la %d utilizatori interni; "
        "revizuiți manual rolurile per utilizator (Angajat/Aprobator/Contabil).",
        len(internal_users),
    )
