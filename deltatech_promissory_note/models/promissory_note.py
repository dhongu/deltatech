# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Get the logger
_logger = logging.getLogger(__name__)


class PromissoryNote(models.Model):
    _name = "promissory.note"
    _description = "Promissory Note"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    _order = "date_due"

    state = fields.Selection(
        [("not_cashed", "Not Cashed"), ("cashed", "Cashed"), ("cancel", "Cancelled")],
        default="not_cashed",
        string="Status",
        copy=False,
        tracking=True,
    )

    type = fields.Selection(
        [("vendor", "Vendor"), ("customer", "Customer")], required=True, default="customer", string="Type"
    )

    agreement = fields.Char(string="Agreement")

    name = fields.Char(
        string="Series and number",
        required=True,
        index=True,
    )

    date_due = fields.Date(string="Due Date", required=True, index=True)

    issuer_id = fields.Many2one("res.partner", string="Issuer", required=True)
    beneficiary_id = fields.Many2one("res.partner", string="Beneficiary", required=True)

    invoice_id = fields.Many2one("account.move", string="Invoice", domain=[("move_type", "!=", "entry")])

    amount = fields.Float(string="Amount", digits="Account", required=True)

    cashed_amount = fields.Float(string="Cashed Amount", digits="Account")
    cashed_date = fields.Date(string="Cashed Date")

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
    )

    acc_issuer = fields.Char("Bank Account Issuer", size=64, required=False)
    acc_beneficiary = fields.Char("Bank Account Beneficiary", size=64, required=False)

    # bank_issuer = fields.Char("Bank Issuer", size=64, readonly=True, required=False)
    # bank_beneficiary = fields.Char("Bank Beneficiary", size=64, required=False)

    bank_issuer_id = fields.Many2one("res.bank", string="Bank Issuer", required=False)
    bank_beneficiary_id = fields.Many2one("res.bank", string="Bank Beneficiary", required=False)

    note = fields.Text(string="Comments")

    is_last_bo = fields.Boolean("Last note", default=False)

    @api.onchange("type")
    def onchange_type(self) -> None:
        if self.type == "customer":
            if self.beneficiary_id != self.env.company.partner_id:
                self.issuer_id = self.beneficiary_id
            else:
                self.issuer_id = False
            self.beneficiary_id = self.env.company.partner_id
        else:
            if self.issuer_id != self.env.company.partner_id:
                self.beneficiary_id = self.issuer_id
            else:
                self.beneficiary_id = False
            self.issuer_id = self.env.company.partner_id

    @api.onchange("issuer_id")
    def onchange_issuer_id(self) -> None:
        if self.issuer_id and self.issuer_id.bank_ids:
            self.acc_issuer = self.issuer_id.bank_ids[0].acc_number
            self.bank_issuer_id = self.issuer_id.bank_ids[0].bank_id
        else:
            self.acc_issuer = False

    @api.onchange("beneficiary_id")
    def onchange_beneficiary_id(self) -> None:
        if self.issuer_id and self.beneficiary_id.bank_ids:
            self.acc_beneficiary = self.beneficiary_id.bank_ids[0].acc_number
            self.bank_beneficiary_id = self.beneficiary_id.bank_ids[0].bank_id
        else:
            self.acc_beneficiary = False

    def action_not_cashed(self) -> None:
        self.write({"state": "not_cashed"})

    @api.constrains("amount")
    def _check_values(self) -> None:
        for promissory in self:
            if promissory.amount <= 0.0:
                raise UserError(_("The <Value> field must be greater than 0!"))

    def _track_subtype(self, init_values: dict) -> models.Model:
        self.ensure_one()
        if "state" in init_values and self.state == "cashed":
            return self.env.ref("deltatech_promissory_note.mt_state_cashed")
        return super()._track_subtype(init_values)

    def action_cashed(self) -> None:
        self.write({"state": "cashed"})
        if self.is_last_bo:
            users = self.env["res.users"].search([])
            for user in users:
                if user.has_group("deltatech_promissory_note.bo_notifications"):
                    name = self.name
                    issuer_name = self.issuer_id.name
                    date = self.date_due
                    cashed_amount = self.cashed_amount
                    agreement = self.agreement
                    subject = _(f"BO - the last - %{name} for {issuer_name} has been cashed")
                    msg = _(
                        f"The last promissory note cashed: {name}, date: {date}. Issuer: {issuer_name}, amount: {cashed_amount}, agreement: {agreement}"
                    )
                    partner_id = user.partner_id.id

                    self.message_post(body=msg, subject=subject, partner_ids=[partner_id])

                    _logger.info(f"BO_LOG: mail sent for BO {name}")

    def action_cancel(self) -> None:
        self.write({"state": "cancel"})
