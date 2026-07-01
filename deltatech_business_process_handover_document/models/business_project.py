from odoo import api, fields, models


class BusinessProject(models.Model):
    _inherit = "business.project"

    handover_stage_id = fields.Many2one(
        "business.process.implementation.stage",
        string="Handover Stage Filter",
        help="If set, the handover document only includes processes (and their tests) "
        "in this implementation stage. Leave empty to include all processes.",
    )
    handover_process_ids = fields.Many2many(
        "business.process",
        string="Handover Processes",
        compute="_compute_handover_process_ids",
        store=True,
        help="Processes included in the handover document, after applying the stage filter.",
    )

    handover_development_ids = fields.Many2many(
        "business.development",
        string="Handover Developments",
        compute="_compute_handover_development_ids",
        help="Developments included in the handover document. When a stage filter is set, only "
        "developments attached to the filtered processes' steps are listed; otherwise all project "
        "developments are listed (unchanged behaviour).",
    )

    @api.depends("process_ids", "process_ids.implementation_stage_id", "handover_stage_id")
    def _compute_handover_process_ids(self):
        for project in self:
            processes = project.process_ids
            if project.handover_stage_id:
                processes = processes.filtered(
                    lambda p, stage=project.handover_stage_id: p.implementation_stage_id == stage
                )
            project.handover_process_ids = processes

    @api.depends(
        "development_ids",
        "handover_stage_id",
        "handover_process_ids",
        "handover_process_ids.development_ids",
    )
    def _compute_handover_development_ids(self):
        for project in self:
            if project.handover_stage_id:
                # Developments live on the process steps; the stage lives on the
                # process, so scope developments through the filtered processes.
                project.handover_development_ids = project.handover_process_ids.development_ids
            else:
                project.handover_development_ids = project.development_ids

    provider_company = fields.Char(string="Provider Company")
    provider_representative = fields.Many2one(
        "res.partner",
        string="Provider Representative",
        domain="[('is_company', '=', False)]",
    )

    recipient_company = fields.Char(string="Recipient Company")
    recipient_representative = fields.Many2one(
        "res.partner",
        string="Recipient Representative",
        domain="[('is_company', '=', False)]",
    )

    provider_testers = fields.Many2many("res.partner", string="Provider Testers", relation="tester_provider")
    recipient_testers = fields.Many2many("res.partner", string="Recipient Testers", relation="tester_recipient")

    development_ids = fields.One2many(
        "business.development",
        "project_id",
        string="Developments",
        compute="_compute_development_ids",
        store=True,
    )

    def _compute_development_ids(self):
        for project in self:
            project.development_ids = self.env["business.development"].search([("project_id", "=", project.id)])
