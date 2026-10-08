# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import ast

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

# names a formula may use besides the line codes
FORMULA_FUNCTIONS = {"abs", "max", "min", "round"}


class AccountMoveTemplate(models.Model):
    _name = "account.move.template"
    _description = "Journal Entry Template"
    _order = "sequence, name"
    _check_company_auto = True

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    journal_id = fields.Many2one(
        "account.journal",
        required=True,
        check_company=True,
        domain="[('type', '=', 'general')]",
        default=lambda self: self._default_journal(),
    )
    ref = fields.Char(string="Reference", help="Default reference of the generated entries.")
    note = fields.Text(string="Instructions", help="Shown to the user in the generation wizard.")
    line_ids = fields.One2many("account.move.template.line", "template_id", string="Lines", copy=True)
    move_count = fields.Integer(compute="_compute_move_count", string="Entries")

    _name_company_uniq = models.Constraint(
        "unique(name, company_id)",
        "A template with this name already exists in this company.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        templates._check_lines()
        return templates

    def write(self, vals):
        res = super().write(vals)
        if "line_ids" in vals:
            self._check_lines()
        return res

    @api.model
    def _default_journal(self):
        return self.env["account.journal"].search(
            [*self.env["account.journal"]._check_company_domain(self.env.company), ("type", "=", "general")],
            limit=1,
        )

    def _compute_move_count(self):
        groups = self.env["account.move"]._read_group(
            [("move_template_id", "in", self.ids)], ["move_template_id"], ["__count"]
        )
        counts = {template.id: count for template, count in groups}
        for template in self:
            template.move_count = counts.get(template.id, 0)

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        if not (default or {}).get("name"):
            for template, vals in zip(self, vals_list, strict=True):
                vals["name"] = self.env._("%s (copy)", template.name)
        return vals_list

    # ------------------------------------------------------------------
    # Validation and computation
    # ------------------------------------------------------------------

    def _line_dependencies(self, line):
        """Return the codes the amount of ``line`` depends on."""
        if line.amount_type == "percent":
            return {line.base_code}
        if line.formula and line.amount_type in ("formula", "input"):
            try:
                tree = ast.parse(line.formula or "", mode="eval")
            except SyntaxError as err:
                raise ValidationError(
                    self.env._(
                        "The formula of line %(code)s is not valid: %(formula)s",
                        code=line.code,
                        formula=line.formula,
                    )
                ) from err
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            return names - FORMULA_FUNCTIONS
        return set()

    def _sorted_lines(self):
        """Lines without the balance line, ordered so that each line comes after the lines it uses."""
        self.ensure_one()
        lines = self.line_ids.filtered(lambda line: line.amount_type != "balance")
        codes = {line.code: line for line in lines}
        balance_codes = set(self.line_ids.filtered(lambda line: line.amount_type == "balance").mapped("code"))
        pending = {}
        for line in lines:
            dependencies = self._line_dependencies(line)
            if line.code in dependencies:
                raise ValidationError(self.env._("Line %s cannot use its own amount.", line.code))
            if dependencies & balance_codes:
                raise ValidationError(
                    self.env._(
                        "Line %s cannot use the balance line: its amount is known only after all the other lines.",
                        line.code,
                    )
                )
            unknown = dependencies - set(codes)
            if unknown:
                raise ValidationError(
                    self.env._(
                        "Line %(code)s uses unknown codes: %(unknown)s",
                        code=line.code,
                        unknown=", ".join(sorted(unknown)),
                    )
                )
            pending[line] = dependencies
        ordered = self.env["account.move.template.line"]
        done = set()
        while pending:
            ready = [line for line, dependencies in pending.items() if dependencies <= done]
            if not ready:
                raise ValidationError(
                    self.env._(
                        "The lines %s depend on each other in a loop.",
                        ", ".join(sorted(line.code for line in pending)),
                    )
                )
            for line in ready:
                ordered |= line
                done.add(line.code)
                del pending[line]
        return ordered

    def _check_lines(self):
        for template in self:
            codes = template.line_ids.mapped("code")
            duplicates = {code for code in codes if codes.count(code) > 1}
            if duplicates:
                raise ValidationError(self.env._("The line codes must be unique: %s", ", ".join(sorted(duplicates))))
            if len(template.line_ids.filtered(lambda line: line.amount_type == "balance")) > 1:
                raise ValidationError(self.env._("A template can have only one balance line."))
            if not template.line_ids.filtered("account_id"):
                raise ValidationError(self.env._("The template %s has no line with an account.", template.name))
            template._sorted_lines()

    def _compute_amounts(self, inputs):
        """Compute the amount of each line except the balance line.

        :param inputs: {template line id: amount} for the lines entered by the user;
            an entered line missing here takes its default (formula or amount)
        :return: {template line: amount}, rounded in the company currency;
            the lines without account are only parameters of the computation
        """
        self.ensure_one()
        currency = self.company_id.currency_id
        values = {}
        amounts = {}
        for line in self._sorted_lines():
            if line.amount_type == "input" and line.id in inputs:
                amount = inputs[line.id]
            elif line.amount_type == "input" and not line.formula:
                amount = line.fixed_amount
            elif line.amount_type == "fixed":
                amount = line.fixed_amount
            elif line.amount_type == "percent":
                amount = values[line.base_code] * line.percent / 100.0
            else:  # formula, or the default formula of an entered line
                try:
                    amount = safe_eval(line.formula, dict(values))
                except Exception as err:
                    raise UserError(
                        self.env._(
                            "The formula of line %(code)s could not be computed: %(error)s",
                            code=line.code,
                            error=err,
                        )
                    ) from err
                if not isinstance(amount, int | float):
                    raise UserError(self.env._("The formula of line %s must return a number.", line.code))
            amount = currency.round(amount)
            values[line.code] = amount
            amounts[line] = amount
        return amounts

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_generate(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "deltatech_account_move_template.action_account_move_template_run"
        )
        action["context"] = {"default_template_id": self.id}
        return action

    @api.model
    def action_load_ro_templates(self):
        company = self.env.company
        if company.account_fiscal_country_id.code != "RO":
            raise UserError(self.env._("The Romanian templates need a company with Romania as fiscal country."))
        created, skipped = self.env["account.move.template"]._load_ro_templates(company)
        message = self.env._("%s templates created.", len(created))
        if skipped:
            message += " " + self.env._("Skipped (existing name or missing account): %s", ", ".join(skipped))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": "success" if created else "warning",
                "next": {"type": "ir.actions.act_window_close"}
                if not created
                else {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_view_moves(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        action.update(
            {
                "domain": [("move_template_id", "=", self.id)],
                "context": {"default_move_type": "entry", "search_default_posted": 0},
            }
        )
        return action


class AccountMoveTemplateLine(models.Model):
    _name = "account.move.template.line"
    _description = "Journal Entry Template Line"
    _inherit = ["analytic.mixin"]
    _order = "sequence, id"
    _check_company_auto = True

    template_id = fields.Many2one("account.move.template", required=True, index=True, ondelete="cascade")
    company_id = fields.Many2one(related="template_id.company_id", store=True)
    currency_id = fields.Many2one(related="template_id.currency_id")
    sequence = fields.Integer(default=10)
    code = fields.Char(
        help="Short identifier of the line, used by the percentage and formula lines (e.g. GROSS). "
        "Filled in automatically (L1, L2...) when left empty.",
    )
    name = fields.Char(string="Label")
    account_id = fields.Many2one(
        "account.account",
        check_company=True,
        domain="[('active', '=', True)]",
        help="Leave empty for a parameter of the computation (e.g. an amount including VAT, a rate): "
        "it is entered or computed, but not recorded in the entry.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        check_company=True,
        help="When empty, the line takes the partner chosen in the generation wizard.",
    )
    direction = fields.Selection([("debit", "Debit"), ("credit", "Credit")], required=True, default="debit")
    amount_type = fields.Selection(
        [
            ("input", "Entered"),
            ("fixed", "Fixed"),
            ("percent", "Percentage"),
            ("formula", "Formula"),
            ("balance", "Balance"),
        ],
        string="Amount Type",
        required=True,
        default="input",
        help="Entered: typed in when the entry is generated; the suggested value is the formula, if set, "
        "otherwise the amount below.\n"
        "Fixed: always the amount below.\n"
        "Percentage: a percentage of the line with the base code.\n"
        "Formula: a Python expression on the codes of the other lines, e.g. GROSS * 0.25.\n"
        "Balance: the amount that balances the entry, taxes included.",
    )
    fixed_amount = fields.Monetary(string="Amount", currency_field="currency_id")
    percent = fields.Float(string="Percentage", digits=(16, 4))
    base_code = fields.Char(string="Base Code", help="Code of the line the percentage applies to.")
    formula = fields.Char()
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        check_company=True,
        help="Taxes computed on this line. Odoo adds the tax lines, with their tax grids, to the entry.",
    )
    tax_tag_ids = fields.Many2many(
        "account.account.tag",
        string="Tax Grids",
        domain="[('applicability', '=', 'taxes')]",
        help="Tax grids set directly on the journal item, for the lines without taxes (e.g. a VAT adjustment).",
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.filtered(lambda line: not line.code)._fill_code()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if "code" in vals:
            self.filtered(lambda line: not line.code)._fill_code()
        return res

    def _fill_code(self):
        for line in self.sorted(lambda line: (line.sequence, line.id)):
            used = set(line.template_id.line_ids.mapped("code"))
            index = 1
            while f"L{index}" in used:
                index += 1
            line.code = f"L{index}"

    @api.constrains("code")
    def _check_code(self):
        for line in self.filtered("code"):
            if not line.code.isidentifier() or line.code in FORMULA_FUNCTIONS:
                raise ValidationError(
                    self.env._(
                        "The code %s is not valid: use letters, digits and underscore, starting with a letter.",
                        line.code,
                    )
                )

    @api.constrains("amount_type", "base_code", "formula", "tax_ids", "account_id")
    def _check_amount_type(self):
        for line in self:
            if line.amount_type == "percent" and not line.base_code:
                raise ValidationError(self.env._("Line %s: set the base code of the percentage.", line.code))
            if line.amount_type == "balance" and not line.account_id:
                raise ValidationError(self.env._("Line %s: the balance line needs an account.", line.code))
            if line.tax_ids and not line.account_id:
                raise ValidationError(self.env._("Line %s: a line with taxes needs an account.", line.code))
            if line.amount_type == "formula" and not line.formula:
                raise ValidationError(self.env._("Line %s: set the formula.", line.code))
            if line.amount_type == "balance" and line.tax_ids:
                raise ValidationError(self.env._("Line %s: the balance line cannot have taxes.", line.code))
