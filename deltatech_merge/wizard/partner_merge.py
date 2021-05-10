# Copyright Terrabit Solutions. See LICENSE file for full copyright and licensing details.

from odoo import models


class MergePartnerAutomatic(models.TransientModel):

    _inherit = "base.partner.merge.automatic.wizard"

    def action_merge(self):
        """Merge Contact button. Merge the selected partners, and redirect to
        the end screen (since there is no other wizard line to process.
        Inherited here for security reasons.
        """
        if not self.partner_ids:
            self.write({"state": "finished"})
            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }

        # security
        if self.env.user.has_group("deltatech_merge.group_merge"):
            self._merge(self.partner_ids.ids, self.dst_partner_id, extra_checks=False)
        else:
            self._merge(self.partner_ids.ids, self.dst_partner_id)

        if self.current_line_id:
            self.current_line_id.unlink()

        return self._action_next_screen()
