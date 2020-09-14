# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class CrmClaim(models.Model):
    _inherit = "crm.claim"

    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(
        string="Quantity rejected", digits=dp.get_precision("Product Unit of Measure"), required=True, default=1
    )
    quantity_claimed = fields.Float(
        string="Quantity claimed", digits=dp.get_precision("Product Unit of Measure"), required=True, default=1
    )
    value = fields.Float(string="Amount", digits=dp.get_precision("Account"), store=True, compute="_compute_value")

    user_ids = fields.Many2many("res.users", "crm_claim_team_rel", "claim_id", "user_id", string="Team")

    action_containment_ids = fields.One2many(
        "crm.claim.action", "claim_id", string="Containment actions", domain=[("type", "=", "containment")]
    )
    action_corrective_ids = fields.One2many(
        "crm.claim.action", "claim_id", string="Permanent Corrective actions", domain=[("type", "=", "corrective")]
    )
    action_verification_ids = fields.One2many(
        "crm.claim.action", "claim_id", string="Effectiveness verification", domain=[("type", "=", "verification")]
    )
    action_preventive_ids = fields.One2many(
        "crm.claim.action", "claim_id", string="Preventive actions", domain=[("type", "=", "preventive")]
    )

    action_ids = fields.One2many("crm.claim.action", "claim_id", string="Actions")

    loc_detected = fields.Many2one("crm.claim.loc.detected", string="Detected in")
    comments = fields.Text(string="Comments")

    date_closed = fields.Datetime(readonly=False)
    closed_by_user_id = fields.Many2one("res.users", string="Closed by", track_visibility="onchange")

    # am incercat sa redefinesc cumpurile originale dar nu am mers
    date_action_next_comp = fields.Date(string="Next Action Date", compute="_compute_action_next", store=False)
    action_next_comp = fields.Char(string="Next Action", compute="_compute_action_next", store=False)

    # costs fields
    costs_management = fields.Float(
        string="Cost of complaints management", digits=dp.get_precision("Account"), store=True
    )
    costs_selection = fields.Float(string="Selection costs", digits=dp.get_precision("Account"), store=True)
    costs_logistic = fields.Float(string="Logistic costs", digits=dp.get_precision("Account"), store=True)
    costs_other = fields.Float(string="Other costs", digits=dp.get_precision("Account"), store=True)
    costs_total = fields.Float(
        string="Total costs", digits=dp.get_precision("Account"), store=True, readonly=True, compute="_compute_costs"
    )
    user_uid = fields.Many2one("res.users", string="uid", compute="_compute_uid")
    is_same_user = fields.Boolean(compute="_compute_is_same_user")
    similar_affected = fields.Boolean(string="Are other similar products affected?")
    similar_affected_ids = fields.One2many("crm.claim.product.affected", "claim_id", string="Affected products")

    def _compute_is_same_user(self):
        for claim in self:
            if claim.user_id == claim.user_uid:
                claim.is_same_user = True
            else:
                claim.is_same_user = False

    def _compute_uid(self):
        for claim in self:
            claim.user_uid = claim.env.user.id

    @api.depends("product_id", "quantity")
    def _compute_value(self):
        for claim in self:
            claim.value = claim.quantity * claim.product_id.lst_price

    @api.depends("costs_management", "costs_selection", "costs_logistic", "costs_other")
    def _compute_costs(self):
        for claim in self:
            claim.costs_total = (
                claim.costs_management + claim.costs_selection + claim.costs_logistic + claim.costs_other
            )

    @api.multi
    @api.depends("action_ids")
    def _compute_action_next(self):
        for claim in self:
            # actions = self.env['crm.claim.action'].search(['claim_id','=',claim.id])yyyy-mm-dd
            # print actions
            for action in claim.action_ids:
                # if action.date_deadline > fields.Date.today() and
                # (not claim.date_action_next_comp or action.date_deadline < claim.date_action_next_comp):
                if action.date_deadline and (action.date_deadline > fields.Date.today()):
                    if not claim.date_action_next_comp or action.date_deadline < claim.date_action_next_comp:
                        claim.date_action_next_comp = action.date_deadline
                        claim.action_next_comp = action.name


class CrmClaimAction(models.Model):
    _name = "crm.claim.action"
    _description = "CRM Claim Action"
    _order = "date_deadline"

    claim_id = fields.Many2one("crm.claim", string="Claim", required=True, index=True)
    type = fields.Selection(
        [
            ("containment", "Containment"),
            ("corrective", "Corrective"),
            ("verification", "Verification"),
            ("preventive", "Preventive"),
        ],
        string="Type",
    )
    name = fields.Char(string="Action", required=True)
    user_id = fields.Many2one("res.users", "Responsible", track_visibility="always")
    date_deadline = fields.Date(string="Deadline")

    state = fields.Selection(
        [("draft", "Undone"), ("open", "In Progress"), ("done", "Done")],
        string="Status",
        index=True,
        default="draft",
        copy=False,
    )


class CrmClaimLocDetected(models.Model):
    _name = "crm.claim.loc.detected"
    _description = "CRM Location Detected"

    name = fields.Char(string="Detected", required=True, translate=True)


class CrmClaimProductsAffected(models.Model):
    _name = "crm.claim.product.affected"
    _description = "Products affected"

    claim_id = fields.Many2one("crm.claim")
    product_id = fields.Many2one("product.template", string="Product")
    quantity = fields.Integer(string="Quantity affected")


# class ProductTemplate(models.Model):
#     _inherit = "product.template"
#
#     claim_id = fields.Many2one('crm.claim')
