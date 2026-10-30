# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountEdiDocument(models.Model):
    _inherit = "account.edi.document"

    # Indexed: the column is a foreign key to ir_attachment (ON DELETE SET NULL), so
    # every attachment the cleanups delete makes PostgreSQL look it up here. Without
    # an index that is a full scan of the table per deleted row, which is what pushed
    # a 1000-row DELETE past odoo.sh's 66 s statement limit on a real database.
    attachment_id = fields.Many2one(index="btree_not_null")
