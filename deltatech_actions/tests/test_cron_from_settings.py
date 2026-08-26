# © 2026 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronFromSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.partner = cls.env["res.partner"].create({"name": "Settings Customer"})
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": cls.env.cr.now(),
            }
        )

    def _create_pdf_attachment(self, name, res_model, res_id, days_ago=100):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": res_model,
                "res_id": res_id,
                "type": "binary",
                "datas": base64.b64encode(b"test pdf content"),
                "mimetype": "application/pdf",
            }
        )
        past_dt = datetime.utcnow() - timedelta(days=days_ago)
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past_dt, att.id))
        return att

    def test_invoice_pdf_from_settings_respects_dry_run_default(self):
        att = self._create_pdf_attachment("INV_SETTINGS.pdf", "account.move", self.move.id, days_ago=100)

        # Default deltatech_actions.invoice_pdf_dry_run is True: nothing gets deleted.
        self.env["account.move"].cron_clean_generated_pdfs_from_settings()
        self.assertTrue(att.exists())

        # Flip it off through the same config parameter the settings screen writes.
        self.icp.set_param("deltatech_actions.invoice_pdf_dry_run", "False")
        self.env["account.move"].cron_clean_generated_pdfs_from_settings()
        self.assertFalse(att.exists())

    def test_invoice_pdf_from_settings_respects_max_date_days(self):
        att = self._create_pdf_attachment("INV_RECENT.pdf", "account.move", self.move.id, days_ago=5)
        self.icp.set_param("deltatech_actions.invoice_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.invoice_pdf_max_date_days", "90")

        # 5 days old, cutoff is 90 days: must survive.
        self.env["account.move"].cron_clean_generated_pdfs_from_settings()
        self.assertTrue(att.exists())

    def test_picking_label_from_settings_only_done_toggle(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        self.env.cr.execute("UPDATE stock_picking SET state = 'draft' WHERE id = %s", (picking.id,))
        att = self._create_pdf_attachment("LabelGLS-999.pdf", "stock.picking", picking.id, days_ago=200)

        self.icp.set_param("deltatech_actions.picking_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.picking_pdf_only_done", "True")
        self.icp.set_param("deltatech_actions.picking_pdf_only_cancel", "True")

        # Picking still in draft: the done/cancel-only filter must protect it.
        self.env["stock.picking"].cron_clean_generated_pdfs_from_settings()
        self.assertTrue(att.exists())

        self.env.cr.execute("UPDATE stock_picking SET state = 'done' WHERE id = %s", (picking.id,))
        self.env["stock.picking"].cron_clean_generated_pdfs_from_settings()
        self.assertFalse(att.exists())

    def test_settings_enabled_toggle_writes_cron_active(self):
        cron = self.env.ref("deltatech_actions.ir_cron_delete_pdf_attachments_invoice")
        self.assertFalse(cron.active, "crons must ship disabled by default")

        settings = self.env["res.config.settings"].create({"dt_actions_invoice_pdf_active": True})
        settings.execute()
        self.assertTrue(cron.active, "the settings screen must be able to enable a cron")

        settings2 = self.env["res.config.settings"].create({"dt_actions_invoice_pdf_active": False})
        settings2.execute()
        self.assertFalse(cron.active, "the settings screen must be able to disable a cron again")

    def test_messages_exclude_models_parsed_from_csv(self):
        message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.partner.id,
                "message_type": "comment",
                "subject": "Should survive",
            }
        )
        past_dt = datetime.utcnow() - timedelta(days=100)
        self.env.cr.execute("UPDATE mail_message SET create_date = %s WHERE id = %s", (past_dt, message.id))

        self.icp.set_param("deltatech_actions.messages_dry_run", "False")
        self.icp.set_param("deltatech_actions.messages_exclude_models", "res.partner,project.%")

        self.env["mail.message"].cron_clean_old_messages_from_settings()
        self.assertTrue(message.exists())
