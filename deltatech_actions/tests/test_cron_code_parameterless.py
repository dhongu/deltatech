# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""The cron records live in a ``noupdate="1"`` data file, so their ``code`` is
frozen the day a database is created: any argument written there can never be
changed again without a migration script. Measured on a production instance,
that froze an AWB label cron at ``limit=50, pattern="Label%"`` for months while
the module reported a version whose code no longer had those arguments.

The rule that keeps this from coming back is: cron code carries no arguments,
every parameter is read from Settings. These tests guard that rule.
"""

import ast

from odoo.tests.common import TransactionCase, tagged

CRON_XML_IDS = [
    "ir_cron_delete_xml_attachments",
    "ir_cron_delete_pdf_attachments_invoice",
    "ir_cron_delete_pdf_attachments_sale_order",
    "ir_cron_delete_pdf_attachments_stock_picking",
    "ir_cron_delete_mail_messages",
    "ir_cron_merge_contacts",
    "ir_cron_merge_companies",
    "cron_normalize_company_names",
    "ir_cron_create_missing_reordering_rules",
]


@tagged("post_install", "-at_install")
class TestCronCodeParameterless(TransactionCase):
    def test_cron_code_passes_no_arguments(self):
        for xml_id in CRON_XML_IDS:
            cron = self.env.ref(f"deltatech_actions.{xml_id}", raise_if_not_found=False)
            if not cron:
                continue
            with self.subTest(xml_id=xml_id):
                body = "\n".join(
                    line
                    for line in (cron.sudo().code or "").splitlines()
                    if line.strip() and not line.strip().startswith("#")
                )
                calls = [node for node in ast.walk(ast.parse(body)) if isinstance(node, ast.Call)]
                self.assertTrue(calls, f"{xml_id}: cron code calls nothing")
                for call in calls:
                    arguments = [ast.unparse(arg) for arg in call.args]
                    arguments += [f"{kw.arg}=..." for kw in call.keywords]
                    self.assertFalse(
                        arguments,
                        f"{xml_id}: cron code must not carry arguments ({', '.join(arguments)}) -- a "
                        f"noupdate data file freezes them forever. Read them from Settings instead, "
                        f"in a *_from_settings() entry point.",
                    )

    def test_from_settings_entry_points_exist(self):
        """A parameterless call is only useful if the method it names is really
        there -- a typo in the data file surfaces as a cron failing at 2 a.m."""
        for xml_id in CRON_XML_IDS:
            cron = self.env.ref(f"deltatech_actions.{xml_id}", raise_if_not_found=False)
            if not cron:
                continue
            with self.subTest(xml_id=xml_id):
                body = "\n".join(
                    line
                    for line in (cron.sudo().code or "").splitlines()
                    if line.strip() and not line.strip().startswith("#")
                )
                model = self.env[cron.model_id.model]
                for call in [node for node in ast.walk(ast.parse(body)) if isinstance(node, ast.Call)]:
                    method = ast.unparse(call.func).split(".")[-1]
                    self.assertTrue(
                        hasattr(model, method),
                        f"{xml_id}: {cron.model_id.model} has no method {method}()",
                    )
