from odoo import api, fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    alternative_ids = fields.One2many("mrp.bom.line.alternative", "bom_line_id", string="Alternatives", copy=True)
    alternative_count = fields.Integer(compute="_compute_alternative_count")
    alternative_policy = fields.Selection(
        [
            ("manual", "Manual"),
            ("auto", "Automatic"),
        ],
        string="Substitution",
        default="manual",
        required=True,
        help="Manual: alternatives are chosen by the user on the manufacturing order.\n"
        "Automatic: when the original component is not available, the shortage is covered "
        "from the alternatives, in their order.",
    )

    @api.depends("alternative_ids")
    def _compute_alternative_count(self):
        for line in self:
            line.alternative_count = len(line.alternative_ids)

    def _get_valid_alternatives(self, date):
        self.ensure_one()
        return self.alternative_ids.filtered(lambda a: a._is_valid_on(date))

    def action_open_alternatives(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Alternatives for %s", self.product_id.display_name),
            "res_model": "mrp.bom.line",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(self.env.ref("deltatech_mrp_bom_alternative.mrp_bom_line_view_form_alternative").id, "form")],
            "target": "new",
        }
