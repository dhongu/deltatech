from odoo import models
from odoo.exceptions import UserError


class ValidateAccountMove(models.TransientModel):
    _inherit = "validate.account.move"
    _description = "Validate Account Move"

    def validate_move(self):
        if self._context.get("active_model") == "account.move":
            domain = [("id", "in", self._context.get("active_ids", [])), ("state", "=", "draft")]
            moves = self.env["account.move"].search(domain).filtered("line_ids")
            if moves:
                message = moves.check_data()
                if message:
                    raise UserError(message)
        return super(ValidateAccountMove, self).validate_move()
