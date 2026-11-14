# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    set_as_default = fields.Boolean(
        string="Set as default",
        help="Remember this journal and payment method on the partner and propose them for the next payments.",
    )
    can_set_as_default = fields.Boolean(compute="_compute_can_set_as_default")

    @api.depends("can_edit_wizard", "partner_id")
    def _compute_can_set_as_default(self):
        allowed = self.env.user.has_group("base.group_partner_manager") and self.env.user.has_group(
            "account.group_account_invoice"
        )
        for wizard in self:
            wizard.can_set_as_default = allowed and wizard.can_edit_wizard and bool(wizard.partner_id)

    def _get_partner_default_payment_method_line(self):
        self.ensure_one()
        if not self.can_edit_wizard or not self.partner_id:
            return self.env["account.payment.method.line"]
        partner = self.partner_id.commercial_partner_id.with_company(self.company_id)
        if self.payment_type == "inbound":
            return partner.property_inbound_payment_method_line_id
        return partner.property_outbound_payment_method_line_id

    def _use_partner_default(self):
        """The partner default is used only when the invoices do not have a preferred method."""
        self.ensure_one()
        return not self.line_ids.move_id.preferred_payment_method_line_id

    @api.depends("available_journal_ids")
    def _compute_journal_id(self):
        kept = self.filtered(lambda w: w.journal_id and w.journal_id._origin in w.available_journal_ids._origin)
        res = super()._compute_journal_id()
        for wizard in self - kept:
            if not wizard._use_partner_default():
                continue
            method_line = wizard._get_partner_default_payment_method_line()
            if method_line and method_line.journal_id in wizard.available_journal_ids._origin:
                wizard.journal_id = method_line.journal_id
        return res

    @api.depends("payment_type", "journal_id")
    def _compute_payment_method_line_id(self):
        kept = self.filtered(
            lambda w: w.journal_id
            and w.payment_method_line_id
            and w.payment_method_line_id in w.journal_id._get_available_payment_method_lines(w.payment_type)
        )
        res = super()._compute_payment_method_line_id()
        for wizard in self - kept:
            if not wizard.journal_id or not wizard._use_partner_default():
                continue
            method_line = wizard._get_partner_default_payment_method_line()
            available = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)
            if method_line and method_line.id in available.ids:
                wizard.payment_method_line_id = method_line
        return res

    def _create_payments(self):
        payments = super()._create_payments()
        if self.set_as_default and self.can_set_as_default:
            self._set_partner_default_payment_method_line()
        return payments

    def _set_partner_default_payment_method_line(self):
        self.ensure_one()
        method_line = self.payment_method_line_id
        partner = self.partner_id.commercial_partner_id.with_company(self.company_id)
        if self.payment_type == "inbound":
            field_name = "property_inbound_payment_method_line_id"
            label = self.env._("receipts")
        else:
            field_name = "property_outbound_payment_method_line_id"
            label = self.env._("payments")
        if partner[field_name] == method_line:
            return
        partner.write({field_name: method_line.id})
        partner.message_post(
            body=self.env._(
                "Default payment method for %(type)s set to %(method)s (%(journal)s) for company %(company)s.",
                type=label,
                method=method_line.name,
                journal=method_line.journal_id.display_name,
                company=self.company_id.name,
            )
        )
