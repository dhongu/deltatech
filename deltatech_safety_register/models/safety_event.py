# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

INJURY_TYPES = ("injury", "lost_time_injury", "fatal")
LOST_TIME_TYPES = ("lost_time_injury", "fatal")
MANAGER_GROUP = "deltatech_safety_register.group_safety_manager"


class SafetyEvent(models.Model):
    _name = "deltatech.safety.event"
    _description = "Safety Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default="/")
    company_id = fields.Many2one(
        "res.company", required=True, readonly=True, default=lambda self: self.env.company, index=True
    )
    event_type = fields.Selection(
        selection=[
            ("near_miss", "Near miss"),
            ("incident", "Incident (no injury)"),
            ("injury", "Injury (no time lost)"),
            ("lost_time_injury", "Lost-time injury"),
            ("fatal", "Fatal"),
        ],
        string="Type",
        required=True,
        default="near_miss",
        tracking=True,
    )
    is_injury = fields.Boolean(compute="_compute_is_injury", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    location = fields.Char()
    is_commute = fields.Boolean(
        string="Commuting accident",
        help="Accident on the way to or from work (accident de traseu). Not counted in LTIFR.",
        tracking=True,
    )
    employee_id = fields.Many2one("hr.employee", string="Injured employee", check_company=True, tracking=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Injured partner",
        check_company=True,
        help="Injured person who is not an employee (contractor, visitor).",
    )
    injured_name = fields.Char(
        string="Injured person name", help="Use when the person is neither employee nor partner."
    )
    department_id = fields.Many2one("hr.department", compute="_compute_department_id", store=True)
    description = fields.Text()
    root_cause = fields.Text()
    state = fields.Selection(
        selection=[("reported", "Reported"), ("closed", "Closed")],
        string="Status",
        required=True,
        readonly=True,
        default="reported",
        copy=False,
        tracking=True,
    )
    closed_date = fields.Date(readonly=True, copy=False)
    action_ids = fields.One2many("deltatech.safety.action", "event_id", string="Corrective actions")
    open_action_count = fields.Integer(compute="_compute_open_action_count", string="Open actions")

    @api.depends("event_type")
    def _compute_is_injury(self):
        for event in self:
            event.is_injury = event.event_type in INJURY_TYPES

    @api.depends("employee_id")
    def _compute_department_id(self):
        for event in self:
            event.department_id = event.employee_id.department_id

    @api.depends("action_ids.state")
    def _compute_open_action_count(self):
        for event in self:
            event.open_action_count = len(event.action_ids.filtered(lambda a: a.state == "open"))

    @api.constrains("event_type", "employee_id", "partner_id", "injured_name")
    def _check_injured_person(self):
        for event in self:
            if event.is_injury and not (event.employee_id or event.partner_id or event.injured_name):
                raise ValidationError(
                    self.env._(
                        "Event %(name)s is an injury: set the injured person "
                        "(Injured employee, Injured partner or Injured person name).",
                        name=event.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                # the year in the reference is the year of the event, not of its registration
                event_date = fields.Date.to_date(vals.get("date")) or fields.Date.context_today(self)
                sequence = self.env["ir.sequence"].with_context(ir_sequence_date=event_date)
                vals["name"] = sequence.next_by_code("deltatech.safety.event") or "/"
        return super().create(vals_list)

    def _is_safety_manager(self):
        return self.env.su or self.env.user.has_group(MANAGER_GROUP)

    def write(self, vals):
        if not self._is_safety_manager() and self.filtered(lambda e: e.state == "closed"):
            if any(not key.startswith(("message_", "activity_")) for key in vals):
                raise UserError(self.env._("A closed safety event can only be changed by a Safety manager."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_reported(self):
        if self.filtered(lambda e: e.state != "reported"):
            raise UserError(self.env._("Only safety events in state Reported can be deleted."))

    def action_close(self):
        for event in self:
            if event.open_action_count:
                raise UserError(
                    self.env._(
                        "Event %(name)s still has %(count)s open corrective action(s). "
                        "Mark them done before closing the event.",
                        name=event.name,
                        count=event.open_action_count,
                    )
                )
        to_close = self.filtered(lambda e: e.state == "reported")
        if to_close:
            to_close.write({"state": "closed", "closed_date": fields.Date.context_today(self)})
        return True
