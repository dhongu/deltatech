# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    disassembly_allow_reclassification = fields.Boolean(
        string="Disassembly: reclassify goods and materials",
        help="Romanian chart of accounts: allow a disassembly report to turn goods (371) into raw "
        "materials or consumables (30x), or materials of one kind into another (301 <-> 302 <-> 303), "
        "with a direct entry. The chart does not provide these correspondences, so they must be covered "
        "by the accounting policy of the company.",
    )
