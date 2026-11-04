# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from odoo import fields, models


class StockCloseMoves(models.TransientModel):
    _name = "stock.close.moves"
    _description = "Close stock moves until date"

    date = fields.Date(
        string="Close until",
        required=True,
        default=fields.Date.context_today,
        help="Every done stock move of the company dated on or before this day is closed: "
        "its Valuation Active flag is unset.",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    def _get_moves_domain(self):
        self.ensure_one()
        tz = ZoneInfo(self.env.context.get("tz") or self.env.user.tz or "UTC")
        date_limit = datetime.combine(self.date, time.max, tzinfo=tz)
        date_limit = date_limit.astimezone(UTC).replace(tzinfo=None)
        return [
            ("company_id", "=", self.company_id.id),
            ("state", "=", "done"),
            ("date", "<=", date_limit),
            ("l10n_ro_valuation_active", "=", True),
        ]

    def action_close(self):
        self.ensure_one()
        moves = self.env["stock.move"].search(self._get_moves_domain())
        moves.write({"l10n_ro_valuation_active": False})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._("%(count)s stock moves closed.", count=len(moves)),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
