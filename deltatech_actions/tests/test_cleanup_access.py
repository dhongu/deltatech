# © 2026 Deltatech / Terrabit
# Regression tests for ACTIONS-004 (public cleanup bypasses caller authorization)
import base64
from datetime import datetime, timedelta

from odoo.exceptions import AccessError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCleanupAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env,
            login="dt_actions_internal",
            groups="base.group_user,sales_team.group_sale_manager,account.group_account_manager,stock.group_stock_manager",
        )
        cls.admin = new_test_user(cls.env, login="dt_actions_admin", groups="base.group_user,base.group_system")
        partner = cls.env["res.partner"].create({"name": "Cleanup partner"})
        cls.so = cls.env["sale.order"].create({"partner_id": partner.id})

    def _old_pdf(self, name="SO_ACL.pdf"):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "sale.order",
                "res_id": self.so.id,
                "type": "binary",
                "datas": base64.b64encode(b"pdf"),
                "mimetype": "application/pdf",
            }
        )
        self.env.cr.execute(
            "UPDATE ir_attachment SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=30), att.id),
        )
        return att

    def _calls(self, env):
        return [
            lambda: env["sale.order"].cron_clean_generated_pdfs(pattern="SO_ACL%", dry_run=False),
            lambda: env["account.move"].cron_clean_generated_pdfs(dry_run=False),
            lambda: env["stock.picking"].cron_clean_generated_pdfs(dry_run=False),
            lambda: env["account.move"].cron_clean_xml_attachments(dry_run=False),
            lambda: env["mail.message"].cron_clean_old_messages(dry_run=False, exclude_models=["x"]),
            lambda: env["sale.order"].cron_clean_generated_pdfs_from_settings(),
            lambda: env["account.move"].cron_clean_generated_pdfs_from_settings(),
            lambda: env["account.move"].cron_clean_xml_attachments_from_settings(),
            lambda: env["stock.picking"].cron_clean_generated_pdfs_from_settings(),
            lambda: env["mail.message"].cron_clean_old_messages_from_settings(),
        ]

    def test_non_admin_cannot_run_cleanup(self):
        att = self._old_pdf()
        user_env = self.env(user=self.user)
        for call in self._calls(user_env):
            with self.assertRaises(AccessError):
                call()
        self.assertTrue(att.exists(), "a rejected call must not delete anything")

    def test_non_admin_cannot_use_run_now(self):
        with self.assertRaises(AccessError):
            self.env["res.config.settings"].with_user(self.user).browse(1)._dt_actions_run_now("sale_pdf")

    def test_admin_can_run_cleanup(self):
        att = self._old_pdf()
        rows = self.env(user=self.admin)["sale.order"].cron_clean_generated_pdfs(
            pattern="SO_ACL%", max_date_days=1, dry_run=False
        )
        self.assertIn(att.id, [r[0] for r in rows])
        self.assertFalse(att.exists())

    def test_cron_user_can_run_cleanup(self):
        # crons run as base.user_root (not superuser mode): must still be allowed
        root_env = self.env(user=self.env.ref("base.user_root"), su=False)
        att = self._old_pdf()
        root_env["sale.order"].cron_clean_generated_pdfs(pattern="SO_ACL%", max_date_days=1, dry_run=False)
        self.assertFalse(att.exists())
