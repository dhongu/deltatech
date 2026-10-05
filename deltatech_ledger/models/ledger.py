import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class Ledger(models.Model):
    _name = "ledger.ledger"
    _description = "Ledger"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "record_date desc, id desc"

    name = fields.Char(string="Number of Record", default=lambda self: self.env._("New"), copy=False, readonly=True)
    record_date = fields.Date(
        string="Record Date",
        default=lambda self: self._default_record_date(),
        tracking=True,
        copy=False,
        help="A reserved number can be dated later, between the dates of the previous and of the next number.",
    )
    document_number = fields.Char(string="Document Number", tracking=True)
    place_of_origin = fields.Char(string="Place of Origin")
    record_short_description = fields.Text(string="Record Short Description")
    record_type = fields.Selection(
        [("entry", "Entry"), ("exit", "Exit")], string="Record Type", required=True, tracking=True
    )
    contact_id = fields.Many2one("res.partner", string="Contact", tracking=True)
    state = fields.Selection(
        [("reserved", "Reserved"), ("active", "Active"), ("canceled", "Canceled")],
        string="State",
        default="active",
        required=True,
        copy=False,
        tracking=True,
    )
    cancel_reason = fields.Text(string="Cancellation Reason", copy=False, readonly=True)
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    sequence_year = fields.Integer(
        string="Register Year", compute="_compute_sequence_year", store=True, help="Year of the number series."
    )
    date_min = fields.Date(string="Earliest Date", compute="_compute_date_limits")
    date_max = fields.Date(string="Latest Date", compute="_compute_date_limits")
    has_duplicate = fields.Boolean(string="Possible Duplicate", compute="_compute_has_duplicate")
    link_ids = fields.One2many("ledger.link", "ledger_id", string="Links")

    @api.model
    def _default_record_date(self):
        # a reservation is dated later, a regular record is dated today
        if self.env.context.get("default_state", "active") == "active":
            return fields.Date.context_today(self)
        return False

    @api.model
    def _add_missing_default_values(self, values):
        res = super()._add_missing_default_values(values)
        if values.get("state") == "reserved" and "record_date" not in values:
            res["record_date"] = False
        return res

    @api.depends("name", "record_date")
    def _compute_sequence_year(self):
        for rec in self:
            match = re.match(r"^(\d{4})/", rec.name or "")
            if match:
                rec.sequence_year = int(match.group(1))
            else:
                rec.sequence_year = (rec.record_date or fields.Date.context_today(rec)).year

    def _get_neighbors(self):
        """Return the nearest dated records before and after this one in the register
        (same company and year, ordered by number). Records without a date are skipped."""
        self.ensure_one()
        # in a form with unsaved changes the record is virtual: use the saved one
        record_id = self._origin.id or self.id
        if not isinstance(record_id, int):
            return self.browse(), self.browse()
        domain = [
            ("id", "!=", record_id),
            ("company_id", "=", self.company_id.id),
            ("sequence_year", "=", self.sequence_year),
            ("record_date", "!=", False),
        ]
        previous = self.search([*domain, ("name", "<", self.name)], order="name desc", limit=1)
        following = self.search([*domain, ("name", ">", self.name)], order="name asc", limit=1)
        return previous, following

    @api.depends("name", "company_id", "sequence_year")
    def _compute_date_limits(self):
        for rec in self:
            previous, following = rec._get_neighbors()
            rec.date_min = previous.record_date or fields.Date.from_string(f"{rec.sequence_year}-01-01")
            rec.date_max = following.record_date or fields.Date.from_string(f"{rec.sequence_year}-12-31")

    @api.depends("document_number", "contact_id", "record_type", "company_id", "state")
    def _compute_has_duplicate(self):
        for rec in self:
            rec.has_duplicate = bool(
                rec.document_number
                and rec.state != "canceled"
                and self.search_count(
                    [
                        ("id", "!=", rec._origin.id),
                        ("state", "!=", "canceled"),
                        ("document_number", "=", rec.document_number),
                        ("record_type", "=", rec.record_type),
                        ("contact_id", "=", rec.contact_id.id),
                        ("company_id", "=", rec.company_id.id),
                    ],
                    limit=1,
                )
            )

    @api.constrains("state", "record_date")
    def _check_active_has_date(self):
        for rec in self:
            if rec.state == "active" and not rec.record_date:
                raise ValidationError(self.env._("Record %s must have a date.", rec.name))

    @api.constrains("record_date", "name", "company_id")
    def _check_record_date(self):
        for rec in self:
            if not rec.record_date:
                continue
            if rec.record_date.year != rec.sequence_year:
                raise ValidationError(
                    self.env._(
                        "The date of record %(name)s must be in %(year)s, the year of its number.",
                        name=rec.name,
                        year=rec.sequence_year,
                    )
                )
            previous, following = rec._get_neighbors()
            if previous and rec.record_date < previous.record_date:
                raise ValidationError(
                    self.env._(
                        "Record %(name)s cannot be dated before %(date)s, the date of the previous number %(previous)s.",
                        name=rec.name,
                        date=fields.Date.to_string(previous.record_date),
                        previous=previous.name,
                    )
                )
            if following and rec.record_date > following.record_date:
                raise ValidationError(
                    self.env._(
                        "Record %(name)s cannot be dated after %(date)s, the date of the next number %(following)s.",
                        name=rec.name,
                        date=fields.Date.to_string(following.record_date),
                        following=following.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        today = fields.Date.context_today(self)
        for vals in vals_list:
            if vals.get("state", "active") == "active" and not vals.get("record_date"):
                vals["record_date"] = today
            if not vals.get("name") or vals["name"] == self.env._("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("ledger.ledger", sequence_date=today) or self.env._(
                    "New"
                )
        return super().create(vals_list)

    def action_confirm(self):
        """Turn a reservation into a regular record."""
        reserved = self.filtered(lambda rec: rec.state == "reserved")
        for rec in reserved:
            if not rec.record_date:
                raise UserError(self.env._("Set the record date before registering %s.", rec.name))
        reserved.write({"state": "active"})

    def action_cancel_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel"),
            "res_model": "ledger.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_ledger_ids": self.ids},
        }

    def action_cancel(self, reason=None):
        """The number stays in the register, marked as canceled."""
        to_cancel = self.filtered(lambda rec: rec.state in ("reserved", "active"))
        to_cancel.write({"state": "canceled", "cancel_reason": reason or False})

    def action_reactivate(self):
        if not self.env.user.has_group("deltatech_ledger.group_ledger_manager"):
            raise AccessError(self.env._("Only a Ledger Manager can reactivate a canceled record."))
        for rec in self.filtered(lambda r: r.state == "canceled"):
            rec.write({"state": "active" if rec.record_date else "reserved", "cancel_reason": False})
