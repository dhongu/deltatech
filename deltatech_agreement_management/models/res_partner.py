# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import operator as py_operator

from odoo import api, fields, models

OPERATORS = {
    "=": py_operator.eq,
    "!=": py_operator.ne,
    "<": py_operator.lt,
    "<=": py_operator.le,
    ">": py_operator.gt,
    ">=": py_operator.ge,
    "in": lambda count, values: count in values,
    "not in": lambda count, values: count not in values,
}


class Partner(models.Model):
    _inherit = "res.partner"

    # Both the count and the search follow the access rights and the access restrictions (ir.access) of
    # general.agreement: a user without access sees 0 and no partner "with agreement".
    agreement_count = fields.Integer(
        string="Agreements",
        compute="_compute_agreements_no",
        search="_search_agreement",
    )

    def view_agreements(self):
        self.ensure_one()
        action = {
            "name": self.env._("Agreement"),
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "general.agreement",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
        return action

    @api.model
    def _get_agreement_counts(self, domain):
        """Return {partner_id: number of agreements} for the agreements visible to the user."""
        Agreement = self.env["general.agreement"]
        if not Agreement.has_access("read"):
            return {}
        groups = Agreement._read_group(domain + [("partner_id", "!=", False)], ["partner_id"], ["__count"])
        return {partner.id: count for partner, count in groups}

    @api.model
    def _search_agreement(self, operator, value):
        if operator not in OPERATORS:
            return NotImplemented
        if operator in ("in", "not in"):
            value = {int(v or 0) for v in value}
        else:
            value = int(value or 0)
        match = OPERATORS[operator]
        counts = self._get_agreement_counts([])
        if match(0, value):
            # partners without agreements match too: exclude the partners whose count does not match
            return [("id", "not in", [pid for pid, count in counts.items() if not match(count, value)])]
        return [("id", "in", [pid for pid, count in counts.items() if match(count, value)])]

    def _compute_agreements_no(self):
        counts = self._get_agreement_counts([("partner_id", "in", self.ids)]) if self.ids else {}
        for partner in self:
            partner.agreement_count = counts.get(partner.id, 0)
