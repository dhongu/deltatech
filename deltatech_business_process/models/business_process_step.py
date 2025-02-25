# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessProcessStep(models.Model):
    _name = "business.process.step"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Business process step"
    _order = "sequence, code, id"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    code = fields.Char(
        string="Code",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    state = fields.Selection(related="process_id.state", copy=False, store=True)

    description = fields.Text(
        string="Description",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    process_id = fields.Many2one(
        string="Process",
        comodel_name="business.process",
        required=True,
        ondelete="cascade",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    area_id = fields.Many2one(related="process_id.area_id", store=True)
    sequence = fields.Integer(
        string="Sequence",
        required=True,
        default=10,
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    responsible_id = fields.Many2one(
        string="Responsible Step",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    development_ids = fields.Many2many(
        string="Developments",
        comodel_name="business.development",
        relation="business_development_step_rel",
        column1="step_id",
        column2="development_id",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    transaction_id = fields.Many2one(
        string="Transaction",
        comodel_name="business.transaction",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    transaction_type = fields.Selection(related="transaction_id.transaction_type")
    role_id = fields.Many2one(
        string="Role",
        comodel_name="business.role",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    details = fields.Html()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code", False):
                vals["code"] = self.env["ir.sequence"].sudo().next_by_code(self._name)
        result = super().create(vals_list)
        return result

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [(step.id, "{}{}".format(step.code and "[%s] " % step.code or "", step.name)) for step in self]
