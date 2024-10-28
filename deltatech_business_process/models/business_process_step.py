# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessProcessStep(models.Model):
    _name = "business.process.step"
    _description = "Business process step"
    _order = "sequence, code, id"

    name = fields.Char(
        string="Name",
        required=True,
    )
    code = fields.Char(
        string="Code",
    )

    state = fields.Selection(related="process_id.state", copy=False, store=True)

    description = fields.Text(
        string="Description",
    )
    process_id = fields.Many2one(
        string="Process",
        comodel_name="business.process",
        # required=True,
        ondelete="cascade",
    )
    area_id = fields.Many2one(related="process_id.area_id", store=True)
    sequence = fields.Integer(
        string="Sequence",
        required=True,
        default=10,
    )

    responsible_id = fields.Many2one(
        string="Responsible Step",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
    )

    development_ids = fields.Many2many(
        string="Developments",
        comodel_name="business.development",
        relation="business_development_step_rel",
        column1="step_id",
        column2="development_id",
    )

    transaction_id = fields.Many2one(
        string="Transaction",
        comodel_name="business.transaction",
    )
    transaction_type = fields.Selection(related="transaction_id.transaction_type")
    role_id = fields.Many2one(
        string="Role",
        comodel_name="business.role",
    )

    details = fields.Html()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code", False):
                vals["code"] = self.env["ir.sequence"].next_by_code(self._name)
        return super().create(vals_list)

    def _compute_display_name(self):
        for step in self:
            step.display_name = "{}{}".format(step.code and f"[{step.code}] " or "", step.name)
