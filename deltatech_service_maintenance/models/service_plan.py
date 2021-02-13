# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceCycle(models.Model):
    _inherit = "service.cycle"

    unit = fields.Selection(selection_add=[("counter", "From counter")], string="Unit Of Measure")

    @api.model
    def get_cyle(self):
        self.ensure_one()
        if self.unit == "counter":
            return self.value
        else:
            return super(ServiceCycle, self).get_cyle()


class ServicePlan(models.Model):
    _name = "service.plan"
    _description = "Service Plan"

    name = fields.Char(string="Reference", readonly=True, default="/")
    equipment_id = fields.Many2one(
        "service.equipment",
        string="Equipment",
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    cycle_id = fields.Many2one(
        "service.cycle", string="Cycle", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    unit = fields.Selection(related="cycle_id.unit")
    start_date = fields.Date(
        string="Start Date",
        default=lambda *a: fields.Date.today(),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    start_counter = fields.Float(
        string="Start counter",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="The counter reading which the schedule should be started.",
    )

    meter_id = fields.Many2one("service.meter", string="Meter", readonly=True, states={"draft": [("readonly", False)]})

    horizon = fields.Integer(
        string="Call horizon",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="The call horizon determines when a service order should be generated for a service call",
    )

    period = fields.Integer(
        string="Scheduling Period",
        readonly=True,
        default=365,
        states={"draft": [("readonly", False)]},
        help="Length of time in days for which the system creates  calls during plan scheduling",
    )

    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("stopped", "Stopped")],
        default="draft",
        string="Status",
        readonly=True,
    )

    reason_id = fields.Many2one(
        "service.order.reason", string="Reason", readonly=True, states={"draft": [("readonly", False)]}
    )
    order_type_id = fields.Many2one(
        "service.order.type", string="Order Type", readonly=True, states={"draft": [("readonly", False)]}
    )

    call_ids = fields.One2many("service.plan.call", "plan_id", string="Plan Calls", readonly=True)

    last_call_done_date = fields.Date(
        string="Date Last Call Done", readonly=True, related="last_call_done_id.completion_date"
    )
    last_call_done_id = fields.Many2one("service.plan.call", string="Last Call Done", readonly=True)

    last_call_id = fields.Many2one("service.plan.call", string="Last Call", readonly=True, compute="_compute_last_call")

    def _compute_last_call(self):
        for plans in self:
            if plans:
                call = self.env["service.plan.call"].search(
                    [("plan_id", "=", plans.id), ("state", "in", ["called", "skipped", "completion"])],
                    order="plan_date DESC",
                    limit=1,
                )
                if call:
                    plans.last_call_id = call

    @api.model
    def create(self, vals):
        if ("name" not in vals) or (vals.get("name") in ("/", False)):
            sequence_plan = self.env.ref("deltatech_service_maintenance.sequence_plan")
            if sequence_plan:
                vals["name"] = self.env["ir.sequence"].next_by_id(sequence_plan.id)
        return super(ServicePlan, self).create(vals)

    def action_start(self):
        self.write({"state": "active"})
        self.rescheduling()

        return True

    def action_stop(self):
        self.write({"state": "stopped"})
        return True

    def action_draft(self):
        self.write({"state": "draft"})
        return True

    def action_restart(self):
        self.rescheduling()
        self.write({"state": "active"})
        return True

    def action_rescheduling(self):
        self.rescheduling()
        return True

    def call_next(self):
        """
        Face urmatorul apel din lista
        """
        for plan in self:
            for call in plan.call_ids:
                if call.state == "called":
                    return call
                if call.state == "draft":
                    call.action_call()
                    return call
        return False

    def rescheduling(self):
        # determin data de starsit de planificare

        # TODO: de facut transformarea in zile a intervalului acum se presupune ca intervalul este in zile

        for plan in self:
            if plan.state != "active":
                return False

            end_date = datetime.today() + timedelta(days=plan.period)  # de ce rezulta datetime ?
            end_date = end_date.date()
            call = plan.last_call_id

            if call:
                if call.completion_date:
                    start_date = fields.Date.from_string(call.completion_date)
                else:
                    start_date = fields.Date.from_string(call.plan_date)
                if call.completion_counter:
                    plan_counter = call.completion_counter
                else:
                    plan_counter = call.plan_counter

                sequence = call.sequence
            else:
                plan_counter = plan.start_counter
                sequence = 1
                start_date = fields.Date.from_string(plan.start_date)

            if plan.unit == "counter":
                plan_counter = plan_counter + plan.cycle_id.value
                next_date = fields.Date.from_string(plan.meter_id.get_forcast_date(plan_counter))
            else:
                next_date = start_date + plan.cycle_id.get_cyle()

            call_ids = self.env["service.plan.call"].search([("plan_id", "=", plan.id), ("state", "=", "draft")])

            call_ids.unlink()

            sequence = sequence + 1

            while next_date < end_date:
                call_date = next_date - timedelta(days=plan.horizon)
                self.env["service.plan.call"].create(
                    {
                        "plan_id": plan.id,
                        "sequence": sequence,
                        "call_date": fields.Date.to_string(call_date),
                        "plan_date": fields.Date.to_string(next_date),
                        "plan_counter": plan_counter,
                    }
                )
                if plan.unit == "counter":
                    plan_counter = plan_counter + plan.cycle_id.value
                    next_date = fields.Date.from_string(plan.meter_id.get_forcast_date(plan_counter))
                else:
                    next_date = next_date + plan.cycle_id.get_cyle()

                sequence = sequence + 1

            plan.call_next()

        return True


class ServicePlanCall(models.Model):
    _name = "service.plan.call"
    _description = "Service Plan Call"
    _order = "plan_id, plan_date"

    name = fields.Char(string="Name", compute="_compute_name")
    sequence = fields.Integer(
        string="Sequence",
        readonly=True,
        index=True,
        help="Gives the sequence order when displaying a list of plan call.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),  # statusul in care se calculeza data planificata si data de apel
            ("called", "Called"),  # statusul in care sistemul a generat un apel si asteapata confirmare
            ("completion", "Completion"),  # statusul in care trece apelul dupa confirmarea executiei.
            ("skipped", "Skipped"),  # statusul in care trece apelul daca nu se mai executa comanda
        ],
        string="State",
        readonly=True,
        default="draft",
    )

    plan_id = fields.Many2one(
        "service.plan",
        required=True,
        string="Plan",
        readonly=True,
    )

    order_id = fields.Many2one(
        "service.order",
        string="Order",
        readonly=True,
    )

    call_date = fields.Date(
        string="Call Date", required=True, readonly=True, index=True, help="Date on which the system creates an order"
    )
    plan_date = fields.Date(
        string="Planned Date",
        required=True,
        readonly=True,
        index=True,
        help="Planned date describes the time at which an order is to be executed.",
    )
    plan_counter = fields.Float(
        string="Planned Counter",
        required=True,
        readonly=True,
        index=True,
        help="Planned counter describes the value of counter at which an order is to be executed.",
    )
    completion_date = fields.Date(
        string="Completion Date",
        readonly=True,
        states={"called": [("readonly", False)]},
        help="Date on which the maintenance date was completed",
    )
    completion_counter = fields.Float(
        string="Completion Counter",
        readonly=True,
        states={"called": [("readonly", False)]},
        help="Value of counter which the maintenance date was completed",
    )

    def _compute_name(self):
        for plan_call in self:
            plan_call.name = plan_call.plan_id.name + " - " + str(plan_call.sequence)

    def action_call(self):
        order = self.env["service.order"].create(
            {
                "date": self.plan_date,
                "equipment_id": self.plan_id.equipment_id.id,
                "reason_id": self.plan_id.reason_id.id,
                "plan_call_id": self.id,
                "type_id": self.plan_id.order_type_id.id,
            }
        )
        self.write({"state": "called", "order_id": order.id})

        return True

    def action_complete(self):
        if self.order_id.state != "done":
            raise UserError(_("Please select close order %s.") % self.order_id.name)
        self.write({"state": "completion"})
        for call in self:
            if not call.completion_date:
                call.write({"completion_date": call.plan_date})
            if not call.completion_counter:
                call.write({"completion_counter": call.plan_counter})
            call.plan_id.write({"last_call_done_id": call.id})

        return True

    def action_skip(self):
        self.write({"state": "skipped"})
        for call in self:
            call.plan_id.action_rescheduling()
        return True
