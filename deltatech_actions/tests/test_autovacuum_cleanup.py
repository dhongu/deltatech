# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""A neutralized database -- every staging build restored on odoo.sh -- has all its
crons switched off by base/data/neutralize.sql, except base.autovacuum_job. Another
module's neutralize.sql cannot switch one back on either: neutralize_database()
iterates the installed modules in the arbitrary order Postgres returns them, so
base's blanket disable may run last. Hanging the cleanups off the autovacuum job is
therefore the only order-independent way a restored copy can tidy itself up.
"""

import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAutovacuumCleanup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.partner = cls.env["res.partner"].create({"name": "Autovacuum Customer"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def _old_pdf(self, name, days_ago=200):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "sale.order",
                "res_id": self.order.id,
                "type": "binary",
                "datas": base64.b64encode(b"pdf"),
                "mimetype": "application/pdf",
            }
        )
        past = datetime.utcnow() - timedelta(days=days_ago)
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past, att.id))
        self.env["ir.attachment"].invalidate_model(["create_date"])
        return att

    def test_disabled_by_default(self):
        """The switch is off unless someone sets it, so adding the hook changes
        nothing for an existing customer."""
        self.icp.search([("key", "=", "deltatech_actions.autovacuum_enabled")]).unlink()
        att = self._old_pdf("Oferta - S0001.pdf")
        self.assertIsNone(self.env["sale.order"]._gc_generated_pdfs())
        self.assertTrue(att.exists(), "autovacuum deleted an attachment while switched off")

    def test_enabled_deletes_and_reports_progress(self):
        self.icp.set_param("deltatech_actions.autovacuum_enabled", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "2")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        self.icp.set_param("deltatech_actions.sale_pdf_pattern", "")
        kept = self._old_pdf("Recent offer.pdf", days_ago=1)
        self._old_pdf("Oferta - S0002.pdf")
        self._old_pdf("Oferta - S0003.pdf")

        done, remaining = self.env["sale.order"]._gc_generated_pdfs()
        self.assertEqual(done, 2, "should delete exactly one batch")
        self.assertTrue(remaining, "hitting the limit must ask the autovacuum job to requeue")
        self.assertTrue(kept.exists(), "an attachment newer than the threshold must survive")

    def test_dry_run_never_asks_to_be_requeued(self):
        """A dry run selects the same rows on every call. If it reported work
        remaining, _run_vacuum_cleaner would spin on it until the cron ran out of
        time, starving every other vacuum method."""
        self.icp.set_param("deltatech_actions.autovacuum_enabled", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "1")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        att = self._old_pdf("Oferta - S0004.pdf")

        done, remaining = self.env["sale.order"]._gc_generated_pdfs()
        self.assertEqual(done, 1)
        self.assertFalse(remaining, "a dry run must never report work remaining")
        self.assertTrue(att.exists(), "a dry run must not delete")

    def test_hooks_are_registered_as_autovacuum(self):
        """_run_vacuum_cleaner finds these only through the decorator."""
        from odoo.addons.base.models.ir_autovacuum import is_autovacuum

        for model in ("sale.order", "account.move", "stock.picking"):
            with self.subTest(model=model):
                func = type(self.env[model])._gc_generated_pdfs
                self.assertTrue(is_autovacuum(func), f"{model}._gc_generated_pdfs is not an autovacuum method")
