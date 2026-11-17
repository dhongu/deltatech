# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

# Traffic light of an indicator and of a pillar. "none" means no data.
WCM_STATES = [
    ("green", "Green"),
    ("yellow", "Yellow"),
    ("red", "Red"),
    ("none", "No data"),
]


class WcmPillar(models.Model):
    _name = "wcm.pillar"
    _description = "WCM Pillar"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True, help="Technical key of the pillar.")
    sequence = fields.Integer(default=10)
    indicator_ids = fields.One2many("wcm.indicator", "pillar_id", string="Indicators")
    indicator_count = fields.Integer(compute="_compute_dashboard")
    green_count = fields.Integer(compute="_compute_dashboard")
    yellow_count = fields.Integer(compute="_compute_dashboard")
    red_count = fields.Integer(compute="_compute_dashboard")
    state = fields.Selection(WCM_STATES, compute="_compute_dashboard")

    _code_uniq = models.Constraint("unique(code)", "The pillar code must be unique.")

    @api.depends("indicator_ids.state")
    def _compute_dashboard(self):
        for pillar in self:
            states = pillar.indicator_ids.mapped("state")
            pillar.indicator_count = len(states)
            pillar.green_count = states.count("green")
            pillar.yellow_count = states.count("yellow")
            pillar.red_count = states.count("red")
            # The pillar shows its worst indicator: red, then yellow, then green.
            if pillar.red_count:
                pillar.state = "red"
            elif pillar.yellow_count:
                pillar.state = "yellow"
            elif pillar.green_count:
                pillar.state = "green"
            else:
                pillar.state = "none"

    def action_open_indicators(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "wcm.indicator",
            "view_mode": "list,form",
            "domain": [("pillar_id", "=", self.id)],
            "context": {"default_pillar_id": self.id},
        }
