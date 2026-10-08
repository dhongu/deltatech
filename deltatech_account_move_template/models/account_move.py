# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    move_template_id = fields.Many2one(
        "account.move.template",
        string="Entry Template",
        readonly=True,
        copy=False,
        index="btree_not_null",
        help="Template the entry was generated from.",
    )
