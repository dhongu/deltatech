# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class ServiceAgreement(models.Model):
    _name = "service.agreement"
    _description = "Service Agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Reference", index=True, default="/", readonly=True, states={"draft": [("readonly", False)]}, copy=False
    )

    description = fields.Char(string="Description", readonly=True, states={"draft": [("readonly", False)]}, copy=False)

    date_agreement = fields.Date(
        string="Agreement Date",
        default=fields.Date.today,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )

    final_date = fields.Date(string="Final Date", readonly=True, states={"draft": [("readonly", False)]}, copy=False)

    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)
    company_currency_id = fields.Many2one("res.currency", string="Company Currency", related="company_id.currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    type_id = fields.Many2one("service.agreement.type", string="Type", required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("open", "In Progress"), ("closed", "Terminated")],
        string="Status",
        index=True,
        readonly=True,
        default="draft",
        copy=False,
    )

    def contract_close(self):
        return self.write({"state": "closed"})

    def contract_open(self):
        return self.write({"state": "open"})

    def contract_draft(self):
        return self.write({"state": "draft"})

    def unlink(self):
        for item in self:
            if item.state != "draft":
                raise UserError(_("You cannot delete a service agreement which is not draft."))
        return super(ServiceAgreement, self).unlink()

    def get_name(self):
        self.ensure_one()
        if not self.type_id or not self.type_id.sequence_id:
            raise UserError(_("You must provide a type and a type sequence"))
        self.write({"name": self.type_id.sequence_id.next_by_id()})

    def print_agreement(self):
        self.ensure_one()
        if not self.type_id or not self.type_id.print_template_id:
            raise UserError(_("You must provide a type and a type report template"))
        report = self.type_id.print_template_id.report_action(self)
        return report


class ServiceAgreementType(models.Model):
    _name = "service.agreement.type"
    _description = "Service Agreement Type"

    name = fields.Char(string="Type", translate=True)
    sequence_id = fields.Many2one("ir.sequence", string="Sequence")
    print_template_id = fields.Many2one("ir.actions.report", string="Layout", required=True)
