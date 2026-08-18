# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PartnerMergeBatchLine(models.Model):
    _name = "partner.merge.batch.line"
    _description = "One group of duplicates in a merge batch"
    _order = "vat_normalized"

    batch_id = fields.Many2one("partner.merge.batch", required=True, ondelete="cascade", index=True)
    master_id = fields.Many2one(
        "res.partner",
        string="Record kept",
        required=True,
        index=True,
        ondelete="cascade",
        help="Chosen by document volume: most invoices, then most sales orders, then oldest.",
    )
    vat_normalized = fields.Char(string="VAT (normalized)", index=True)
    category = fields.Selection(
        [
            ("A", "A — others empty"),
            ("B", "B — documents on one"),
            ("C", "C — invoices on several"),
            ("D", "D — balance on several"),
        ],
    )
    absorbed_count = fields.Integer(string="Records absorbed")
    absorbed_ids = fields.Char(string="Absorbed IDs")
    absorbed_names = fields.Text(
        string="Absorbed names",
        help="Captured before the merge: afterwards these records no longer exist. Useful when the "
        "kept record carries the degraded name and the correct one was on an absorbed record.",
    )
    master_name = fields.Char(related="master_id.name", string="Kept name", store=False)
    name_suspect = fields.Boolean(
        compute="_compute_name_suspect",
        string="Name looks degraded",
        help="The kept record is chosen by document volume, not by name quality, so sometimes the "
        "surviving name is the one mangled at import. Check these by hand after the merge.",
    )

    def _compute_name_suspect(self):
        import re

        run_together = re.compile(r"[a-zà-ſ][A-ZÀ-ž]")
        only_digits = re.compile(r"^[A-Z]{0,2}[0-9]{4,}$")
        for line in self:
            name = line.master_id.name or ""
            line.name_suspect = bool(
                only_digits.match(name) or (" " not in name and (run_together.search(name) or len(name) > 8))
            )
