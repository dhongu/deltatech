# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Move the cleanup crons off hardcoded call arguments.

The cron records ship in ``data/ir_cron_data.xml``, which is ``noupdate="1"``
-- deliberately, so an upgrade never re-enables a cron the customer turned off,
nor resets its schedule. The side effect is that the ``code`` field of an
already-created cron is frozen at whatever the module wrote the day it was
installed. So when 19.0.0.3.0 replaced the argument-carrying calls with
parameterless ``*_from_settings()`` entry points, every existing database kept
running the old inline arguments, and the Settings screen became decorative:
its values are read only by ``*_from_settings()``, which nothing called.

Measured on a production instance (PTC, 27.08.2026): module reported
19.0.0.5.0, yet the AWB label cron was still executing
``cron_clean_generated_pdfs(limit=50, pattern="Label%", max_date_days=90)``
-- a limit 5x smaller than the daily inflow and a pattern that misses 42% of
the real label names -- while ``ir.config_parameter`` held zero
``deltatech_actions.*`` keys. Nothing failed, nothing was logged: the crons ran
green every night and deleted almost nothing.

This script rewrites the ``code`` of the existing records, and -- so the switch
does not silently change what the cron deletes -- first copies the arguments it
finds in the old code into the matching system parameters. Rule: an argument
written explicitly in the old call wins; an argument the old call did not pass
keeps the module default (which, where they differ, only ever narrows the
deletion set -- e.g. AWB labels are now restricted to done/cancelled
transfers). Parameters already present in the database are never overwritten.
"""

import ast
import logging

_logger = logging.getLogger(__name__)

PREFIX = "deltatech_actions."

# xml_id -> (new parameterless code, {old kwarg: system parameter suffix})
CRONS = {
    "ir_cron_delete_xml_attachments": (
        "# parameters: Settings > General Settings > Database Cleanup > Duplicate XML attachments\n"
        "model.cron_clean_xml_attachments_from_settings()",
        {
            "limit": "xml_limit",
            "duplicates": "xml_duplicates",
            "max_attachments_to_delete": "xml_max_delete",
            "max_date_days": "xml_max_date_days",
            "dry_run": "xml_dry_run",
        },
    ),
    "ir_cron_delete_pdf_attachments_invoice": (
        "# parameters: Settings > General Settings > Database Cleanup > Invoice PDF cleanup\n"
        "model.cron_clean_generated_pdfs_from_settings()",
        {
            "limit": "invoice_pdf_limit",
            "pattern": "invoice_pdf_pattern",
            "max_date_days": "invoice_pdf_max_date_days",
            "dry_run": "invoice_pdf_dry_run",
        },
    ),
    "ir_cron_delete_pdf_attachments_sale_order": (
        "# parameters: Settings > General Settings > Database Cleanup > Sale order PDF cleanup\n"
        "model.cron_clean_generated_pdfs_from_settings()",
        {
            "limit": "sale_pdf_limit",
            "pattern": "sale_pdf_pattern",
            "max_date_days": "sale_pdf_max_date_days",
            "dry_run": "sale_pdf_dry_run",
        },
    ),
    "ir_cron_delete_pdf_attachments_stock_picking": (
        "# parameters: Settings > General Settings > Database Cleanup > AWB label cleanup\n"
        "model.cron_clean_generated_pdfs_from_settings()",
        {
            "limit": "picking_pdf_limit",
            "pattern": "picking_pdf_pattern",
            "max_date_days": "picking_pdf_max_date_days",
            "dry_run": "picking_pdf_dry_run",
        },
    ),
    "ir_cron_delete_mail_messages": (
        "# parameters: Settings > General Settings > Database Cleanup > Old messages cleanup\n"
        "model.cron_clean_old_messages_from_settings()",
        {
            "limit": "messages_limit",
            "pattern": "messages_pattern",
            "max_date_days": "messages_max_date_days",
            "dry_run": "messages_dry_run",
            "exclude_models": "messages_exclude_models",
        },
    ),
    "ir_cron_merge_contacts": (
        "# parameters: Settings > General Settings > Database Cleanup > Duplicate contacts merge\n"
        "model._cron_merge_duplicate_contacts_from_settings()",
        {"limit": "merge_contacts_limit"},
    ),
    "ir_cron_merge_companies": (
        "# parameters: Settings > General Settings > Database Cleanup > Duplicate companies merge\n"
        "model._cron_merge_duplicate_companies_from_settings()",
        {"limit": "merge_companies_limit"},
    ),
}


def _parse_old_kwargs(code):
    """Return the keyword arguments of the call in ``code``, or None if the code
    is not a plain single call we can read. Comment lines are dropped first --
    the shipped code carries a leading ``# params:`` block."""
    body = "\n".join(line for line in (code or "").splitlines() if line.strip() and not line.strip().startswith("#"))
    if not body.strip():
        return None
    try:
        tree = ast.parse(body.strip())
    except SyntaxError:
        return None
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    if len(calls) != 1:
        # Hand-edited cron with several statements: leave the arguments alone
        # rather than guess which call is the relevant one.
        return None
    kwargs = {}
    for keyword in calls[0].keywords:
        if not keyword.arg:
            continue
        try:
            kwargs[keyword.arg] = ast.literal_eval(keyword.value)
        except (ValueError, SyntaxError):
            _logger.warning("Cannot read cron argument %s, it keeps the module default", keyword.arg)
    return kwargs


def _as_param(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (list, tuple)):
        return ",".join(str(item) for item in value)
    return str(value)


def _code_location(cr, cron_id):
    """Return (table, row id) holding the cron's ``code``.

    Since 19.0 ``ir.cron`` delegates to ``ir.actions.server``, so ``code`` is a
    column of ``ir_act_server``, reachable only through
    ``ir_cron.ir_actions_server_id`` -- ``UPDATE ir_cron SET code`` fails
    outright. The older layout is still handled, so this script does not break
    if it is ever replayed on a pre-delegation database.
    """
    cr.execute(
        """SELECT 1 FROM information_schema.columns
           WHERE table_name = 'ir_cron' AND column_name = 'code'"""
    )
    if cr.fetchone():
        return "ir_cron", cron_id
    cr.execute("SELECT ir_actions_server_id FROM ir_cron WHERE id = %s", (cron_id,))
    row = cr.fetchone()
    return ("ir_act_server", row[0]) if row and row[0] else (None, None)


def migrate(cr, version):
    if not version:
        return

    for xml_id, (new_code, param_map) in CRONS.items():
        cr.execute(
            "SELECT res_id FROM ir_model_data WHERE module = 'deltatech_actions' AND name = %s",
            (xml_id,),
        )
        row = cr.fetchone()
        if not row:
            continue
        cron_id = row[0]

        table, code_id = _code_location(cr, cron_id)
        if not table:
            continue
        # Table name comes from _code_location, never from data.
        cr.execute(f"SELECT code FROM {table} WHERE id = %s", (code_id,))  # pylint: disable=sql-injection
        row = cr.fetchone()
        if not row:
            continue
        old_code = row[0] or ""
        if "_from_settings" in old_code:
            continue

        kwargs = _parse_old_kwargs(old_code)
        if kwargs is None:
            _logger.warning(
                "Cron %s was edited by hand and is left untouched; its arguments must be moved "
                "to Settings > General Settings > Database Cleanup manually:\n%s",
                xml_id,
                old_code.strip(),
            )
            continue

        seeded = {}
        for kwarg, suffix in param_map.items():
            if kwarg not in kwargs:
                continue
            key = PREFIX + suffix
            cr.execute("SELECT id FROM ir_config_parameter WHERE key = %s", (key,))
            if cr.fetchone():
                # Someone already set it from the Settings screen: their value wins.
                continue
            value = _as_param(kwargs[kwarg])
            cr.execute(
                """INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
                   VALUES (%s, %s, 1, 1, NOW(), NOW())""",
                (key, value),
            )
            seeded[suffix] = value

        cr.execute(f"UPDATE {table} SET code = %s WHERE id = %s", (new_code, code_id))  # pylint: disable=sql-injection
        _logger.info(
            "Cron %s now reads its parameters from Settings; carried over: %s",
            xml_id,
            ", ".join(f"{k}={v}" for k, v in sorted(seeded.items())) or "nothing (module defaults apply)",
        )
