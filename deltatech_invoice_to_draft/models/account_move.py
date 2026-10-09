# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import sys

from odoo import models
from odoo.exceptions import AccessError

# Modules whose functions dispatch a public model method called remotely: the web client
# (call_kw / call_button), XML-RPC / JSON-RPC (execute_kw) and the Odoo 19 /json/2 API.
_RPC_DISPATCH_MODULES = ("odoo.service.model", "odoo.addons.rpc.controllers.json2")
# Public methods that reset a posted move as their own action: called remotely, they are
# the user's request to reset, so the frames below them do not count as an internal caller.
_RESET_METHODS = ("button_draft", "button_cancel", "button_draft_cancel")


def _is_rpc_entry_point():
    """True when ``button_draft`` was requested by a remote call, not by server code.

    The frames of the reset methods (``button_draft`` override chain, ``button_cancel``
    on a posted move) are skipped; the first other frame is the caller. Native flows that
    reset a move internally (payment back to draft or cancelled, unlink, bank
    reconciliation undo, POS session closing, ...) have their own method as caller and
    are left alone.
    """
    frame = sys._getframe(2)
    while frame is not None and frame.f_code.co_name in _RESET_METHODS:
        frame = frame.f_back
    return frame is not None and frame.f_globals.get("__name__") in _RPC_DISPATCH_MODULES


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_show_reset_to_draft_button(self):
        res = super()._compute_show_reset_to_draft_button()
        access = self.env.user.has_group("deltatech_invoice_to_draft.group_reset_to_draft_account_move")
        for move in self:
            move.show_reset_to_draft_button = move.show_reset_to_draft_button and access
        return res

    def _check_reset_to_draft_access(self):
        if self.env.su or self.env.user.has_group("deltatech_invoice_to_draft.group_reset_to_draft_account_move"):
            return
        raise AccessError(self.env._("Your user is not allowed to reset journal entries to draft."))

    def button_draft(self):
        if _is_rpc_entry_point():
            self._check_reset_to_draft_access()
        return super().button_draft()

    def button_draft_cancel(self):
        self._check_reset_to_draft_access()
        self.button_draft()
        self.button_cancel()
