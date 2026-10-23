# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from itertools import combinations

from odoo import api, fields, models

# the standard merge wizard refuses more contacts at once
MERGE_WIZARD_LIMIT = 3


class PartnerDuplicateGroup(models.Model):
    _name = "partner.duplicate.group"
    _description = "Group of probably duplicated partners"
    _order = "state, score desc, id"

    scan_id = fields.Many2one("partner.duplicate.scan", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    partner_ids = fields.Many2many(
        "res.partner",
        "partner_duplicate_group_partner_rel",
        "group_id",
        "partner_id",
        string="Partners",
        help="Remove from the group the partners that are not duplicates before merging.",
    )
    partner_count = fields.Integer(string="Partners left", compute="_compute_partner_count")
    score = fields.Integer(readonly=True, help="Strongest match in the group, from 0 to 100.")
    reasons = fields.Text(readonly=True)
    match_type = fields.Selection(
        [("exact", "Same VAT, phone or email"), ("fuzzy", "Similar name")],
        readonly=True,
    )
    state = fields.Selection(
        [("new", "To review"), ("merged", "Merged"), ("ignored", "Not duplicates")],
        default="new",
        readonly=True,
    )

    @api.depends("partner_ids.name")
    def _compute_display_name(self):
        for group in self:
            names = group.partner_ids[:MERGE_WIZARD_LIMIT].mapped("display_name")
            more = len(group.partner_ids) - len(names)
            group.display_name = ", ".join(names) + (f" +{more}" if more > 0 else "") or str(group.id)

    @api.depends("partner_ids", "partner_ids.active")
    def _compute_partner_count(self):
        for group in self:
            group.partner_count = len(group.partner_ids.filtered("active"))

    def _refresh_state(self):
        """A merge done with the standard wizard deletes the absorbed partners: the group is done
        when fewer than two active partners are left in it."""
        for group in self.filtered(lambda g: g.state == "new"):
            if len(group.partner_ids.filtered("active")) < 2:
                group.state = "merged"

    def action_merge(self):
        """Opens the standard merge wizard on the group, at most three partners at a time —
        the wizard's own limit. Re-open it until the group is done."""
        self.ensure_one()
        self._refresh_state()
        if self.state != "new":
            # no exception: it would roll back the state just refreshed
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": self.env._("Nothing left to merge in this group."),
                    "type": "info",
                    "next": {"type": "ir.actions.client", "tag": "soft_reload"},
                },
            }
        partners = self.partner_ids.filtered("active").sorted("id")[:MERGE_WIZARD_LIMIT]
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Merge Contacts"),
            "res_model": "base.partner.merge.automatic.wizard",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": {"active_model": "res.partner", "active_ids": partners.ids},
        }

    def action_ignore(self):
        self.env["partner.duplicate.ignore"]._add_pairs(self._pairs())
        self.write({"state": "ignored"})
        return True

    def action_reopen(self):
        """Back to review; the pairs marked as not duplicates are forgotten."""
        self.env["partner.duplicate.ignore"]._remove_pairs(self._pairs())
        self.write({"state": "new"})
        self._refresh_state()
        return True

    def action_open_partners(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Partners"),
            "res_model": "res.partner",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", self.partner_ids.ids)],
        }

    def _pairs(self):
        return {pair for group in self for pair in combinations(sorted(group.partner_ids.ids), 2)}


class PartnerDuplicateIgnore(models.Model):
    _name = "partner.duplicate.ignore"
    _description = "Pair of partners marked as not duplicates"

    partner_a_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True)
    partner_b_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True)

    _pair_uniq = models.Constraint(
        "UNIQUE(partner_a_id, partner_b_id)",
        "This pair is already marked as not duplicates.",
    )
    _pair_ordered = models.Constraint(
        "CHECK(partner_a_id < partner_b_id)",
        "The first partner of the pair must have the smaller id.",
    )

    def _add_pairs(self, pairs):
        if not pairs:
            return self.browse()
        existing = {(r.partner_a_id.id, r.partner_b_id.id) for r in self.search(self._pairs_domain(pairs))}
        return self.create([{"partner_a_id": a, "partner_b_id": b} for a, b in sorted(set(pairs) - existing)])

    def _remove_pairs(self, pairs):
        if pairs:
            self.search(self._pairs_domain(pairs)).filtered(
                lambda r: (r.partner_a_id.id, r.partner_b_id.id) in pairs
            ).unlink()

    @api.model
    def _pairs_domain(self, pairs):
        return [
            ("partner_a_id", "in", list({a for a, _b in pairs})),
            ("partner_b_id", "in", list({b for _a, b in pairs})),
        ]
