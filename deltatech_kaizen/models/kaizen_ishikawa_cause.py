# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from odoo import fields, models


class KaizenIshikawaCause(models.Model):
    _name = "kaizen.ishikawa.cause"
    _description = "Kaizen Ishikawa Cause"
    _order = "project_id, category, sequence, id"

    project_id = fields.Many2one("kaizen.project", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    category = fields.Selection(
        [
            ("man", "Man"),
            ("machine", "Machine"),
            ("method", "Method"),
            ("material", "Material"),
            ("measurement", "Measurement"),
            ("environment", "Environment"),
        ],
        required=True,
        default="man",
    )
    name = fields.Char(required=True)
