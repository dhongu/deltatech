# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class AccountMoveTemplateRun(models.TransientModel):
    _name = "account.move.template.run"
    _description = "Generate Journal Entry from Template"
    _check_company_auto = True

    template_id = fields.Many2one("account.move.template", required=True, check_company=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    note = fields.Text(related="template_id.note")
    date = fields.Date(required=True, default=fields.Date.context_today)
    ref = fields.Char(string="Reference", compute="_compute_ref", store=True, readonly=False)
    partner_id = fields.Many2one(
        "res.partner",
        check_company=True,
        help="Set on the template lines that have no partner.",
    )
    line_ids = fields.One2many(
        "account.move.template.run.line",
        "wizard_id",
        string="Amounts",
        compute="_compute_line_ids",
        store=True,
        readonly=False,
    )
    post = fields.Boolean(string="Post the Entry")

    @api.depends("template_id")
    def _compute_ref(self):
        for wizard in self:
            wizard.ref = wizard.template_id.ref

    @api.depends("template_id")
    def _compute_line_ids(self):
        for wizard in self:
            commands = [Command.clear()]
            for line in wizard.template_id.line_ids.filtered(lambda line: line.amount_type == "input"):
                commands.append(
                    Command.create(
                        {"template_line_id": line.id, "amount": line.fixed_amount, "use_default": bool(line.formula)}
                    )
                )
            wizard.line_ids = commands
            wizard._update_default_amounts()

    @api.onchange("line_ids")
    def _onchange_line_ids(self):
        self._update_default_amounts()

    def _get_inputs(self):
        return {run_line.template_line_id.id: run_line.amount for run_line in self.line_ids if not run_line.use_default}

    def _update_default_amounts(self):
        """Show the suggested amounts of the entered lines that keep their default formula."""
        for wizard in self:
            default_lines = wizard.line_ids.filtered("use_default")
            if not default_lines or not wizard.template_id:
                continue
            try:
                amounts = wizard.template_id._compute_amounts(wizard._get_inputs())
            except UserError:
                continue
            for run_line in default_lines:
                run_line.amount = amounts.get(run_line.template_line_id, 0.0)

    def _prepare_move(self):
        return {
            "move_type": "entry",
            "journal_id": self.template_id.journal_id.id,
            "date": self.date,
            "ref": self.ref,
            "company_id": self.company_id.id,
            "move_template_id": self.template_id.id,
        }

    def _prepare_move_line(self, line, amount):
        # a negative amount goes on the other side
        balance = amount if line.direction == "debit" else -amount
        vals = {
            "name": line.name or self.ref or self.template_id.name,
            "account_id": line.account_id.id,
            "partner_id": (line.partner_id or self.partner_id).id,
            "balance": balance,
        }
        if line.analytic_distribution:
            vals["analytic_distribution"] = line.analytic_distribution
        if line.tax_ids:
            vals["tax_ids"] = [Command.set(line.tax_ids.ids)]
        if line.tax_tag_ids:
            vals["tax_tag_ids"] = [Command.set(line.tax_tag_ids.ids)]
        return vals

    def _create_move(self):
        self.ensure_one()
        template = self.template_id
        currency = self.company_id.currency_id
        amounts = template._compute_amounts(self._get_inputs())
        line_commands = [
            Command.create(self._prepare_move_line(line, amounts[line]))
            for line in template.line_ids
            if line in amounts and line.account_id and not currency.is_zero(amounts[line])
        ]
        if not line_commands:
            raise UserError(self.env._("All the amounts are zero: there is nothing to record."))

        move_vals = self._prepare_move()
        move_vals["line_ids"] = line_commands
        # Odoo adds the tax lines and, when they unbalance the entry, an automatic balancing line
        # on the suspense account: the balance line of the template takes its place
        move = self.env["account.move"].with_context(check_move_validity=False).create(move_vals)
        move = move.with_context(check_move_validity=True)
        lines = move.line_ids.sorted("id")
        own_lines = lines[: len(line_commands)]
        automatic_line = (lines - own_lines).filtered(lambda line: not line.tax_line_id)
        residual = currency.round(sum((lines - automatic_line).mapped("balance")))
        balance_line = template.line_ids.filtered(lambda line: line.amount_type == "balance")
        if currency.is_zero(residual):
            automatic_line.unlink()
        elif not balance_line:
            raise UserError(
                self.env._(
                    "The entry is not balanced: debit minus credit is %(residual)s. "
                    "Check the amounts or add a balance line to the template %(template)s.",
                    residual=residual,
                    template=template.name,
                )
            )
        else:
            amount = residual if balance_line.direction == "credit" else -residual
            vals = self._prepare_move_line(balance_line, amount)
            if automatic_line:
                vals.pop("balance")
                automatic_line.write(vals)
            else:
                move.write({"line_ids": [Command.create(vals)]})
        if self.post:
            move.action_post()
        return move

    def action_generate(self):
        move = self._create_move()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
        }


class AccountMoveTemplateRunLine(models.TransientModel):
    _name = "account.move.template.run.line"
    _description = "Generate Journal Entry from Template - Amount"
    _order = "sequence, id"

    wizard_id = fields.Many2one("account.move.template.run", required=True, ondelete="cascade")
    template_line_id = fields.Many2one("account.move.template.line", required=True, ondelete="cascade")
    sequence = fields.Integer(related="template_line_id.sequence")
    code = fields.Char(related="template_line_id.code")
    name = fields.Char(related="template_line_id.name")
    account_id = fields.Many2one(related="template_line_id.account_id")
    direction = fields.Selection(related="template_line_id.direction")
    currency_id = fields.Many2one(related="wizard_id.currency_id")
    amount = fields.Monetary(currency_field="currency_id")
    use_default = fields.Boolean(
        string="Suggested",
        help="Keep the amount computed by the template formula. Uncheck it to type another amount.",
    )
    has_formula = fields.Boolean(compute="_compute_has_formula")

    @api.depends("template_line_id")
    def _compute_has_formula(self):
        for line in self:
            line.has_formula = bool(line.template_line_id.formula)
