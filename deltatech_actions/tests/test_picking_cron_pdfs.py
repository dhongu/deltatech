# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPickingCronGeneratedPDFs(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a picking to attach files to
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )

    def _create_attachment_for_picking(self, name="PICK_TEST.pdf", days_ago=10, mimetype="application/pdf"):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "stock.picking",
                "res_id": self.picking.id,
                "type": "binary",
                "datas": base64.b64encode(b"test pdf content"),
                "mimetype": mimetype,
            }
        )
        past_dt = datetime.utcnow() - timedelta(days=days_ago)
        self.env.cr.execute(
            "UPDATE ir_attachment SET create_date = %s WHERE id = %s",
            (past_dt, att.id),
        )
        return att

    def test_picking_cron_dry_run_and_delete(self):
        # Two attachments: one matches 'PICK_%' and one other type/mime
        self._create_attachment_for_picking(name="PICK_0001.pdf", days_ago=30)
        self._create_attachment_for_picking(name="PICK_0002.bin", days_ago=30, mimetype="application/octet-stream")
        att_other = self._create_attachment_for_picking(name="OTHER_0001.pdf", days_ago=30)

        # Dry run with pattern 'PICK_%' should return only the two matching ones (pdf and octet-stream)
        self.env["stock.picking"].cron_clean_generated_pdfs(limit=100, pattern="PICK_%", max_date_days=1, dry_run=True)

        # Real delete should remove only the matching ones
        self.env["stock.picking"].cron_clean_generated_pdfs(limit=100, pattern="PICK_%", max_date_days=1, dry_run=False)

        # Empty pattern should catch the remaining one and delete in non-dry run
        rows_all = self.env["stock.picking"].cron_clean_generated_pdfs(
            limit=100, pattern="", max_date_days=1, dry_run=True
        )
        ids_all = {r[0] for r in rows_all}
        self.assertIn(att_other.id, ids_all)

        self.env["stock.picking"].cron_clean_generated_pdfs(limit=100, pattern="", max_date_days=1, dry_run=False)
        self.assertFalse(att_other.exists())

    def test_picking_cron_catches_real_carrier_label_names(self):
        # Real AWB label filenames vary a lot by carrier: some are the
        # carrier's own report name, others are just the raw tracking
        # number, or the field's technical name when a carrier integration
        # does not set one -- none of them start with "Label".
        att_tracking = self._create_attachment_for_picking(name="1ONBLN528391985", days_ago=30)
        att_technical = self._create_attachment_for_picking(name="label_attachment", days_ago=30)

        rows = self.env["stock.picking"].cron_clean_generated_pdfs(limit=100, max_date_days=1, dry_run=True)
        ids = {r[0] for r in rows}
        self.assertIn(att_tracking.id, ids)
        self.assertIn(att_technical.id, ids)

    def test_picking_cron_states_filter(self):
        other_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        self.env.cr.execute("UPDATE stock_picking SET state = 'done' WHERE id = %s", (self.picking.id,))
        self.env.cr.execute("UPDATE stock_picking SET state = 'draft' WHERE id = %s", (other_picking.id,))

        att_done = self._create_attachment_for_picking(name="LabelGLS-1.pdf", days_ago=30)
        att_in_progress = self.env["ir.attachment"].create(
            {
                "name": "LabelGLS-2.pdf",
                "res_model": "stock.picking",
                "res_id": other_picking.id,
                "type": "binary",
                "datas": base64.b64encode(b"test pdf content"),
                "mimetype": "application/pdf",
            }
        )
        past_dt = datetime.utcnow() - timedelta(days=30)
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past_dt, att_in_progress.id))

        rows = self.env["stock.picking"].cron_clean_generated_pdfs(
            limit=100, max_date_days=1, dry_run=True, states=["done", "cancel"]
        )
        ids = {r[0] for r in rows}
        self.assertIn(att_done.id, ids)
        self.assertNotIn(att_in_progress.id, ids)
