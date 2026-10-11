# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL, float_compare, float_is_zero


class StockDisassembly(models.Model):
    _name = "stock.disassembly"
    _description = "Disassembly Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(string="Number", default="/", required=True, readonly=True, copy=False, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done"), ("cancel", "Cancelled")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id")

    product_id = fields.Many2one(
        "product.product",
        string="Disassembled Product",
        required=True,
        check_company=True,
        domain="[('is_storable', '=', True)]",
        tracking=True,
    )
    tracking = fields.Selection(related="product_id.tracking")
    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial Number",
        check_company=True,
        domain="[('product_id', '=', product_id)]",
    )
    product_qty = fields.Float(string="Quantity", digits="Product Unit", required=True, default=1.0, tracking=True)
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Unit",
        compute="_compute_product_uom_id",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        check_company=True,
        domain="[('usage', '=', 'internal')]",
        default=lambda self: self._default_location_id(),
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        compute="_compute_location_dest_id",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
        check_company=True,
        domain="[('usage', '=', 'internal')]",
        help="Default location of the resulting products.",
    )
    scrap_location_id = fields.Many2one(
        "stock.location",
        string="Loss Location",
        compute="_compute_scrap_location_id",
        store=True,
        readonly=False,
        precompute=True,
        check_company=True,
        domain="[('usage', '=', 'inventory')]",
        help="Default location of the loss lines.",
    )
    allocation_method = fields.Selection(
        [
            ("quantity", "Quantity"),
            ("price", "Reference price"),
            ("percent", "Percentage"),
            ("fixed", "Fixed value"),
        ],
        required=True,
        default="price",
        tracking=True,
        help="How the value of the disassembled product is split over the resulting products:\n"
        "- Quantity: in proportion to the quantity, in the unit of each product;\n"
        "- Reference price: in proportion to reference price x quantity;\n"
        "- Percentage: the percentages entered on the lines, which must add up to 100;\n"
        "- Fixed value: the values entered on the lines; the difference goes to the last line.\n"
        "Lines with a fixed value are deducted first, whatever the method; "
        "rounding differences go to the last line.",
    )
    line_ids = fields.One2many("stock.disassembly.line", "disassembly_id", string="Results", copy=True)

    source_value = fields.Monetary(
        string="Actual Cost",
        readonly=True,
        copy=False,
        help="Cost at which the disassembled product left the stock, set at validation.",
    )
    value = fields.Monetary(
        string="Value",
        compute="_compute_value",
        help="Estimated cost of the disassembled product while in draft, actual cost once validated.",
    )
    allocated_value = fields.Monetary(compute="_compute_allocated_value")
    over_norm_value = fields.Monetary(
        string="Loss Above Norm",
        compute="_compute_allocated_value",
        help="Value of the loss above the technological norm: non-deductible expense, "
        "and the input VAT of this part must be adjusted.",
    )
    reason = fields.Text()
    committee = fields.Text(help="Members of the committee, one per line (name, position).")
    move_ids = fields.One2many("stock.move", "disassembly_id", string="Stock Moves", readonly=True)
    move_count = fields.Integer(compute="_compute_move_count")
    account_move_id = fields.Many2one("account.move", string="Journal Entry", readonly=True, copy=False)

    @api.model
    def _default_location_id(self):
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        return warehouse.lot_stock_id

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for disassembly in self:
            disassembly.product_uom_id = disassembly.product_id.uom_id

    @api.depends("location_id")
    def _compute_location_dest_id(self):
        for disassembly in self:
            disassembly.location_dest_id = disassembly.location_id

    @api.depends("company_id")
    def _compute_scrap_location_id(self):
        groups = self.env["stock.location"]._read_group(
            [("company_id", "in", self.company_id.ids), ("usage", "=", "inventory")], ["company_id"], ["id:min"]
        )
        locations = {company.id: location_id for company, location_id in groups}
        for disassembly in self:
            disassembly.scrap_location_id = locations.get(disassembly.company_id.id, False)

    @api.depends("source_value", "state", "product_id", "lot_id", "product_qty", "product_uom_id")
    def _compute_value(self):
        for disassembly in self:
            if disassembly.state == "done":
                disassembly.value = disassembly.source_value
            else:
                disassembly.value = disassembly._estimate_source_value()

    @api.depends("line_ids.value", "line_ids.line_type", "line_ids.over_norm")
    def _compute_allocated_value(self):
        for disassembly in self:
            disassembly.allocated_value = sum(disassembly.line_ids.mapped("value"))
            disassembly.over_norm_value = sum(
                disassembly.line_ids.filtered(lambda line: line.line_type == "scrap").mapped("value")
            )

    @api.depends("move_ids")
    def _compute_move_count(self):
        for disassembly in self:
            disassembly.move_count = len(disassembly.move_ids)

    def _get_source_qty(self):
        """Quantity of the disassembled product in its own unit."""
        self.ensure_one()
        uom = self.product_uom_id or self.product_id.uom_id
        return uom._compute_quantity(self.product_qty, self.product_id.uom_id)

    def _estimate_source_value(self):
        """Cost at which the product would leave the stock now; the actual cost comes from the move."""
        self.ensure_one()
        product = self.product_id.with_company(self.company_id)
        if not product:
            return 0.0
        price = product.standard_price
        if product.lot_valuated and self.lot_id:
            price = self.lot_id.with_company(self.company_id).standard_price
        return self.currency_id.round(price * self._get_source_qty())

    # ------------------------------------------------------------------
    # Cost allocation
    # ------------------------------------------------------------------
    def _get_allocation(self):
        """Split ``value`` over the lines; returns {line: value}.

        A loss within the norm gets nothing: its cost stays in the resulting products. Lines with a
        fixed value (all of them with the *Fixed value* method) are deducted first; the rest is
        shared by the method and the last line takes the rounding difference.
        """
        self.ensure_one()
        currency = self.currency_id
        result = {line: 0.0 for line in self.line_ids}
        valued = self.line_ids.filtered(lambda line: line._is_valued())
        if not valued:
            return result
        if self.allocation_method == "fixed":
            fixed = valued
        else:
            fixed = valued.filtered("use_fixed_value")
        free = valued - fixed
        total = self.value
        for line in fixed:
            result[line] = currency.round(line.fixed_value)
        pool = total - sum(result[line] for line in fixed)
        if not free:
            # only fixed values: the last line takes the difference to the cost
            last = fixed[-1]
            result[last] = currency.round(result[last] + pool)
            return result

        weights = {line: line._get_allocation_weight() for line in free}
        total_weight = sum(weights.values())
        allocated = 0.0
        for index, line in enumerate(free):
            if index == len(free) - 1:
                result[line] = currency.round(pool - allocated)
            else:
                share = weights[line] / total_weight if total_weight else 1.0 / len(free)
                result[line] = currency.round(pool * share)
                allocated += result[line]
        return result

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_cancel(self):
        if any(disassembly.state != "draft" for disassembly in self):
            raise UserError(self.env._("Only draft disassembly reports can be cancelled."))
        self.write({"state": "cancel"})

    def action_draft(self):
        if any(disassembly.state != "cancel" for disassembly in self):
            raise UserError(self.env._("Only cancelled disassembly reports can be reset to draft."))
        self.write({"state": "draft"})

    def unlink(self):
        if any(disassembly.state == "done" for disassembly in self):
            raise UserError(self.env._("A validated disassembly report cannot be deleted."))
        return super().unlink()

    def action_view_moves(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("stock.stock_move_action")
        action["domain"] = [("disassembly_id", "=", self.id)]
        action["context"] = {"create": False}
        return action

    def action_view_account_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.account_move_id.id,
            "view_mode": "form",
        }

    def _lock_for_validation(self):
        """Validate only once: a retried request would take the product out of stock twice."""
        self.ensure_one()
        self.env.cr.execute(SQL("SELECT id FROM stock_disassembly WHERE id = %s FOR UPDATE", self.id))
        self.invalidate_recordset(["state"])
        if self.state != "draft":
            raise UserError(self.env._("The disassembly report %s is not in draft.", self.display_name))

    def _check_before_validate(self):
        self.ensure_one()
        uom = self.product_id.uom_id
        if uom.compare(self.product_qty, 0.0) <= 0:
            raise ValidationError(self.env._("The quantity to disassemble must be positive."))
        if self.date > fields.Date.context_today(self):
            raise ValidationError(self.env._("The date of the disassembly report cannot be in the future."))
        if self.tracking and not self.lot_id:
            raise ValidationError(
                self.env._("Set the lot/serial number of the disassembled product %s.", self.product_id.display_name)
            )
        if self.tracking == "serial" and uom.compare(self._get_source_qty(), 1.0):
            raise ValidationError(self.env._("A product tracked by serial number is disassembled one unit at a time."))
        products = self.line_ids.filtered(lambda line: line.line_type == "product")
        if not products:
            raise ValidationError(self.env._("Add at least one resulting product."))
        real_time = self.product_id.valuation == "real_time"
        mixed = products.filtered(lambda line: (line.product_id.valuation == "real_time") != real_time)
        if mixed:
            raise ValidationError(
                self.env._(
                    "The resulting products %s are not valued like the disassembled product "
                    "(automated or manual valuation): the journal entry would be incomplete.",
                    ", ".join(mixed.product_id.mapped("display_name")),
                )
            )
        for line in self.line_ids:
            line._check_before_validate()
        valued = self.line_ids.filtered(lambda line: line._is_valued())
        if self.allocation_method == "percent":
            free = valued.filtered(lambda line: not line.use_fixed_value)
            if free and float_compare(sum(free.mapped("percent")), 100.0, precision_digits=2):
                raise ValidationError(self.env._("The percentages of the lines must add up to 100."))
        if self.allocation_method == "price":
            free = valued.filtered(lambda line: not line.use_fixed_value)
            if free and not any(free.mapped("reference_price")):
                raise ValidationError(self.env._("Set a reference price on the resulting products."))

    def _check_allocation(self):
        self.ensure_one()
        currency = self.currency_id
        zero_loss = self.line_ids.filtered(
            lambda line: line.line_type == "scrap" and line.over_norm and currency.is_zero(line.value)
        )
        if zero_loss:
            raise UserError(
                self.env._(
                    "The loss above the norm (%s) has no value: give it a fixed value or a percentage, otherwise "
                    "it stays in the cost of the resulting products.",
                    ", ".join(zero_loss.product_id.mapped("display_name")),
                )
            )
        if any(currency.compare_amounts(line.value, 0.0) < 0 for line in self.line_ids):
            raise UserError(
                self.env._(
                    "The fixed values exceed the cost of the disassembled product (%s): "
                    "a resulting product would get a negative value.",
                    currency.format(self.value),
                )
            )
        if not currency.is_zero(sum(self.line_ids.mapped("value")) - self.value):
            raise UserError(self.env._("The values of the lines do not add up to the cost of the product."))

    def action_validate(self):
        for disassembly in self:
            disassembly._lock_for_validation()
            disassembly._check_before_validate()
            disassembly._validate()
        return True

    def _validate(self):
        self.ensure_one()
        if self.name == "/":
            self.name = self.env["ir.sequence"].with_company(self.company_id).next_by_code(
                "stock.disassembly", sequence_date=self.date
            ) or self.env._("New")
        self = self.with_context(force_period_date=self.date)  # noqa: PLW0642

        self._check_account_routes()
        self._create_source_move()
        # the localization may split the move by FIFO layer: the cost is the sum of the pieces
        source_moves = self.move_ids.filtered(lambda move: not move.disassembly_line_id and move.state == "done")
        # the value of a move is signed: negative for an outgoing move
        self.source_value = -sum(source_moves.mapped("value"))
        self._check_allocation()

        result_moves = self.env["stock.move"]
        for line in self.line_ids:
            result_moves |= line._create_move()
        result_moves.picked = True
        result_moves._action_done()

        if self.date != fields.Date.context_today(self):
            moment = datetime.combine(self.date, fields.Datetime.now().time())
            self.move_ids.write({"date": moment})
            self.move_ids.move_line_ids.write({"date": moment})

        self._create_account_move()
        self.state = "done"
        if self.over_norm_value:
            self.message_post(
                body=self.env._(
                    "Loss above the technological norm valued at %s: non-deductible expense. "
                    "Check the adjustment of the input VAT for this part.",
                    self.currency_id.format(self.over_norm_value),
                )
            )

    def _create_source_move(self):
        self.ensure_one()
        move = self.env["stock.move"].create(
            {
                "product_id": self.product_id.id,
                "uom_id": self.product_uom_id.id,
                "product_uom_qty": self.product_qty,
                "location_id": self.location_id.id,
                "location_dest_id": self.product_id.with_company(self.company_id).property_stock_production.id,
                "company_id": self.company_id.id,
                "origin": self.name,
                "disassembly_id": self.id,
            }
        )
        move._action_confirm()
        taken = move._update_reserved_quantity(
            move.product_qty, self.location_id, lot_id=self.lot_id or None, strict=False
        )
        if self.product_id.uom_id.compare(taken, move.product_qty) < 0:
            raise UserError(
                self.env._(
                    "Not enough stock of %(product)s in %(location)s to disassemble %(qty)s %(uom)s.",
                    product=self.product_id.display_name,
                    location=self.location_id.display_name,
                    qty=self.product_qty,
                    uom=self.product_uom_id.name,
                )
            )
        owners = move.move_line_ids.owner_id - self.company_id.partner_id
        if owners:
            raise UserError(
                self.env._(
                    "Stock owned by %s cannot be disassembled: only the own stock of the company.",
                    ", ".join(owners.mapped("display_name")),
                )
            )
        move.picked = True
        move._action_done()
        return move

    # ------------------------------------------------------------------
    # Accounting
    # ------------------------------------------------------------------
    def _is_ro_accounting(self):
        return self.company_id.account_fiscal_country_id.code == "RO"

    @api.model
    def _get_move_accounts(self, move):
        """Product accounts for a stock move, with the location accounts of the localization."""
        return (
            move.product_id.product_tmpl_id.with_company(move.company_id)
            .with_context(l10n_ro_stock_move=move)
            .get_product_accounts()
        )

    def _get_ro_result_account(self):
        account = (
            self.env["account.account"]
            .with_company(self.company_id)
            .search(
                [*self.env["account.account"]._check_company_domain(self.company_id), ("code", "=like", "711%")],
                limit=1,
            )
        )
        if not account:
            raise UserError(self.env._("Account 711 (change in inventories) is missing from the chart of accounts."))
        return account

    def _get_source_expense_account(self, source_move, source_account):
        """Expense of the disassembled product: 60x/607 by its category, 711 for own products (34x)."""
        if self._is_ro_accounting() and (source_account.code or "").startswith("34"):
            return self._get_ro_result_account()
        account = self._get_move_accounts(source_move).get("expense")
        if not account:
            raise UserError(
                self.env._("Set the expense account of the product %s.", source_move.product_id.display_name)
            )
        return account

    # Stock to stock correspondences of the Romanian chart, by synthetic account (3 digits):
    # own products used as materials or sold as goods, materials sold as goods
    RO_DIRECT_ROUTES = {
        ("341", "301"),
        ("341", "302"),
        ("345", "301"),
        ("345", "302"),
        ("345", "303"),
        ("345", "371"),
        ("347", "301"),
        ("347", "302"),
        ("347", "371"),
        ("301", "371"),
        ("302", "371"),
        ("303", "371"),
    }

    def _get_account_route(self, source_account, result_account):
        """How the value goes from the disassembled product to a resulting product.

        ``direct``: stock to stock entry. ``via_result``: the product leaves through its expense
        account and the result enters through 711; the Romanian chart debits 34x only from 711.
        Goods turned into materials (371 -> 30x) and materials of another kind (30x -> 30y) are not
        provided by the chart: they are direct only if the accounting policy allows it. Any other
        pair is refused. Outside Romania the entry is always direct.
        """
        if not self._is_ro_accounting():
            return "direct"
        source, result = (source_account.code or "")[:3], (result_account.code or "")[:3]
        if source == result:
            return "direct"
        if result.startswith("34"):
            return "via_result"
        if (source, result) in self.RO_DIRECT_ROUTES:
            return "direct"
        if (source == "371" or source.startswith("30")) and result.startswith("30"):
            if self.company_id.disassembly_allow_reclassification:
                return "direct"
            raise UserError(
                self.env._(
                    "%(source_account)s cannot become %(result_account)s through a disassembly report: the chart "
                    "of accounts does not provide this correspondence. If the accounting policy of the company "
                    "allows it, enable it in the Inventory settings.",
                    source_account=source_account.display_name,
                    result_account=result_account.display_name,
                )
            )
        raise UserError(
            self.env._(
                "The disassembly from account %(source_account)s into account %(result_account)s is not supported.",
                source_account=source_account.display_name,
                result_account=result_account.display_name,
            )
        )

    def _check_account_routes(self):
        """Refuse an unsupported pair of accounts before any stock is moved."""
        self.ensure_one()
        if self.product_id.valuation != "real_time" or not self._is_ro_accounting():
            return
        Move = self.env["stock.move"]
        production = self.product_id.with_company(self.company_id).property_stock_production
        source_move = Move.new(
            {
                "product_id": self.product_id.id,
                "location_id": self.location_id.id,
                "location_dest_id": production.id,
                "company_id": self.company_id.id,
            }
        )
        source_account = self._get_move_accounts(source_move).get("stock_valuation")
        for line in self.line_ids.filtered(lambda line: line.line_type == "product"):
            result_move = Move.new(
                {
                    "product_id": line.product_id.id,
                    "location_id": production.id,
                    "location_dest_id": line.location_dest_id.id,
                    "company_id": self.company_id.id,
                }
            )
            result_account = self._get_move_accounts(result_move).get("stock_valuation")
            if source_account and result_account:
                self._get_account_route(source_account, result_account)

    def _prepare_account_move_line_vals(self):
        self.ensure_one()
        source_move = self.move_ids.filtered(lambda move: not move.disassembly_line_id)[:1]
        source_account = self._get_move_accounts(source_move).get("stock_valuation")
        if not source_account:
            raise UserError(
                self.env._("Set the stock valuation account of the product %s.", self.product_id.display_name)
            )
        vals_list = []

        def add(debit_account, credit_account, value, line, debit_product, credit_product):
            label = f"{self.name} - {line.product_id.display_name}"
            vals_list.append(
                {
                    "account_id": debit_account.id,
                    "name": label,
                    "debit": value,
                    "credit": 0.0,
                    "product_id": debit_product.id,
                    "quantity": line._get_product_qty() if debit_product == line.product_id else 0.0,
                }
            )
            vals_list.append(
                {
                    "account_id": credit_account.id,
                    "name": label,
                    "debit": 0.0,
                    "credit": value,
                    "product_id": credit_product.id,
                }
            )

        source = self.product_id
        for line in self.line_ids.filtered(lambda line: line._is_valued() and not self.currency_id.is_zero(line.value)):
            if line.line_type == "scrap":
                # loss above the norm: expense of the disassembled product
                expense = self._get_source_expense_account(source_move, source_account)
                add(expense, source_account, line.value, line, source, source)
                continue
            result_account = self._get_move_accounts(line.move_ids[:1]).get("stock_valuation")
            if not result_account:
                raise UserError(
                    self.env._("Set the stock valuation account of the product %s.", line.product_id.display_name)
                )
            if self._get_account_route(source_account, result_account) == "direct":
                add(result_account, source_account, line.value, line, line.product_id, source)
            else:
                expense = self._get_source_expense_account(source_move, source_account)
                add(expense, source_account, line.value, line, source, source)
                add(result_account, self._get_ro_result_account(), line.value, line, line.product_id, line.product_id)
        return vals_list

    def _create_account_move(self):
        """One journal entry for the whole report, instead of one per stock move."""
        self.ensure_one()
        if self.product_id.valuation != "real_time":
            return self.env["account.move"]
        vals_list = self._prepare_account_move_line_vals()
        if not vals_list:
            return self.env["account.move"]
        journal = self.company_id.account_stock_journal_id
        if not journal:
            raise UserError(self.env._("Set the stock journal of the company %s.", self.company_id.name))
        account_move = (
            self.env["account.move"]
            .sudo()
            .create(
                {
                    "move_type": "entry",
                    "journal_id": journal.id,
                    "date": self.date,
                    "ref": self.name,
                    "company_id": self.company_id.id,
                    "line_ids": [fields.Command.create(vals) for vals in vals_list],
                }
            )
        )
        account_move._post()
        self.account_move_id = account_move
        # the scrap moves do not touch the stock (virtual to virtual): the localization cannot type them
        self.move_ids.filtered(
            lambda move: move.disassembly_line_id.line_type != "scrap"
        ).account_move_id = account_move
        return account_move


class StockDisassemblyLine(models.Model):
    _name = "stock.disassembly.line"
    _description = "Disassembly Report Line"
    _order = "disassembly_id, sequence, id"
    _check_company_auto = True

    disassembly_id = fields.Many2one("stock.disassembly", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="disassembly_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="disassembly_id.currency_id")
    state = fields.Selection(related="disassembly_id.state")
    sequence = fields.Integer(default=10)
    line_type = fields.Selection(
        [("product", "Product"), ("scrap", "Loss")],
        string="Type",
        required=True,
        default="product",
        help="Product: enters the stock and gets its share of the value; recoverable waste that is kept "
        "in stock is a product line too.\n"
        "Loss: technological loss or non-recoverable waste, sent to the loss location; within the norm it "
        "gets no value (its cost stays in the resulting products), above the norm it gets its share and is "
        "booked as an expense.",
    )
    product_id = fields.Many2one("product.product", required=True, check_company=True)
    tracking = fields.Selection(related="product_id.tracking")
    quantity = fields.Float(digits="Product Unit", required=True, default=1.0)
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Unit",
        compute="_compute_product_uom_id",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
    )
    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial Number",
        check_company=True,
        domain="[('product_id', '=', product_id)]",
    )
    lot_name = fields.Char(string="New Lot/Serial Number", help="Created at validation if no lot is selected.")
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Destination",
        compute="_compute_location_dest_id",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
        check_company=True,
    )
    over_norm = fields.Boolean(string="Above Norm", help="Loss above the technological norm.")
    reference_price = fields.Float(
        digits="Product Price",
        compute="_compute_reference_price",
        store=True,
        readonly=False,
        precompute=True,
        help="Unit price used to weigh the allocation; by default the cost of the product.",
    )
    percent = fields.Float(string="%", digits=(16, 2))
    use_fixed_value = fields.Boolean(string="Fixed", help="Keep the value entered on this line.")
    fixed_value = fields.Monetary()
    value = fields.Monetary(compute="_compute_value", store=True)
    unit_cost = fields.Float(compute="_compute_value", store=True, digits="Product Price")
    move_ids = fields.One2many("stock.move", "disassembly_line_id", readonly=True)

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    @api.depends("line_type", "disassembly_id.location_dest_id", "disassembly_id.scrap_location_id")
    def _compute_location_dest_id(self):
        for line in self:
            if line.line_type == "scrap":
                line.location_dest_id = line.disassembly_id.scrap_location_id
            else:
                line.location_dest_id = line.disassembly_id.location_dest_id

    @api.depends("product_id")
    def _compute_reference_price(self):
        for line in self:
            line.reference_price = line.product_id.with_company(line.company_id).standard_price

    @api.depends(
        "disassembly_id.value",
        "disassembly_id.allocation_method",
        "disassembly_id.line_ids.line_type",
        "disassembly_id.line_ids.over_norm",
        "disassembly_id.line_ids.product_id",
        "disassembly_id.line_ids.quantity",
        "disassembly_id.line_ids.product_uom_id",
        "disassembly_id.line_ids.reference_price",
        "disassembly_id.line_ids.percent",
        "disassembly_id.line_ids.use_fixed_value",
        "disassembly_id.line_ids.fixed_value",
    )
    def _compute_value(self):
        allocations = {}
        for line in self:
            disassembly = line.disassembly_id
            if disassembly not in allocations:
                allocations[disassembly] = disassembly._get_allocation() if disassembly else {}
            line.value = allocations[disassembly].get(line, 0.0)
            qty = line.quantity
            line.unit_cost = line.value / qty if qty else 0.0

    def _get_product_qty(self):
        self.ensure_one()
        uom = self.product_uom_id or self.product_id.uom_id
        if not self.product_id:
            return self.quantity
        return uom._compute_quantity(self.quantity, self.product_id.uom_id)

    def _is_valued(self):
        self.ensure_one()
        return self.line_type == "product" or self.over_norm

    def _get_allocation_weight(self):
        self.ensure_one()
        method = self.disassembly_id.allocation_method
        if method == "quantity":
            return self._get_product_qty()
        if method == "percent":
            return self.percent
        return self.reference_price * self.quantity

    def _check_before_validate(self):
        self.ensure_one()
        uom = self.product_id.uom_id
        if uom.compare(self.quantity, 0.0) <= 0:
            raise ValidationError(self.env._("The quantity of %s must be positive.", self.product_id.display_name))
        if self.line_type == "product":
            if not self.product_id.is_storable:
                raise ValidationError(
                    self.env._(
                        "The resulting product %s must be tracked in stock, to carry its value.",
                        self.product_id.display_name,
                    )
                )
            if self.location_dest_id.usage != "internal":
                raise ValidationError(
                    self.env._(
                        "The resulting product %s must enter an internal location.", self.product_id.display_name
                    )
                )
        elif self.location_dest_id.usage == "internal":
            raise ValidationError(
                self.env._(
                    "The loss %s goes to a loss location; recoverable waste that enters the stock is a product line.",
                    self.product_id.display_name,
                )
            )
        if self.product_id.is_storable and self.tracking:
            if not self.lot_id and not self.lot_name:
                raise ValidationError(
                    self.env._("Set the lot/serial number of the resulting product %s.", self.product_id.display_name)
                )
            if self.tracking == "serial" and uom.compare(self._get_product_qty(), 1.0):
                raise ValidationError(
                    self.env._(
                        "A product tracked by serial number (%s) is entered one unit per line.",
                        self.product_id.display_name,
                    )
                )

    def _get_or_create_lot(self):
        self.ensure_one()
        if self.lot_id or not self.lot_name or not self.tracking or not self.product_id.is_storable:
            return self.lot_id
        lot = self.env["stock.lot"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("name", "=", self.lot_name),
                *self.env["stock.lot"]._check_company_domain(self.company_id),
            ],
            limit=1,
        )
        if not lot:
            lot = self.env["stock.lot"].create(
                {"name": self.lot_name, "product_id": self.product_id.id, "company_id": self.company_id.id}
            )
        self.lot_id = lot
        return lot

    def _create_move(self):
        self.ensure_one()
        disassembly = self.disassembly_id
        source_location = self.product_id.with_company(self.company_id).property_stock_production
        lot = self._get_or_create_lot()
        move = self.env["stock.move"].create(
            {
                "product_id": self.product_id.id,
                "uom_id": self.product_uom_id.id,
                "product_uom_qty": self.quantity,
                "location_id": source_location.id,
                "location_dest_id": self.location_dest_id.id,
                "company_id": self.company_id.id,
                "origin": disassembly.name,
                "disassembly_id": disassembly.id,
                "disassembly_line_id": self.id,
            }
        )
        move._action_confirm()
        move.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "product_id": self.product_id.id,
                "uom_id": self.product_uom_id.id,
                "quantity": self.quantity,
                "location_id": source_location.id,
                "location_dest_id": self.location_dest_id.id,
                "lot_id": lot.id,
                "company_id": self.company_id.id,
            }
        )
        return move

    @api.constrains("percent")
    def _check_percent(self):
        for line in self:
            if line.percent < 0 or line.percent > 100:
                raise ValidationError(self.env._("A percentage must be between 0 and 100."))

    @api.constrains("fixed_value")
    def _check_fixed_value(self):
        for line in self:
            if float_is_zero(line.fixed_value, precision_rounding=line.currency_id.rounding or 0.01):
                continue
            if line.fixed_value < 0:
                raise ValidationError(self.env._("A fixed value cannot be negative."))
