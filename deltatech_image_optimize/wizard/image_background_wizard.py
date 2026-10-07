# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo import api, fields, models


class ImageBackgroundWizard(models.TransientModel):
    _name = "deltatech.image.background.wizard"
    _description = "Remove Image Background"

    mode = fields.Selection(
        [("preview", "Preview"), ("queue", "Queue")],
        required=True,
        default="preview",
        readonly=True,
    )
    line_ids = fields.One2many("deltatech.image.background.wizard.line", "wizard_id", string="Images")
    image_count = fields.Integer(compute="_compute_counts", string="Selected Images")
    failed_count = fields.Integer(compute="_compute_counts", string="No Product Found")

    @api.depends("line_ids.image_after")
    def _compute_counts(self):
        for wizard in self:
            wizard.image_count = len(wizard.line_ids)
            wizard.failed_count = len(wizard.line_ids.filtered(lambda line: not line.image_after))

    @api.model
    def _dt_create_for(self, targets):
        """Creează wizard-ul pentru recordurile date (o listă de recordseturi, câte unul pe model).

        Până la ``bg_sync_limit`` imagini, fundalul se elimină acum, ca rezultatul
        să poată fi văzut înainte de a fi scris; peste limită, wizard-ul doar
        confirmă trimiterea în coadă.
        """
        params = self.env["ir.attachment"]._dt_bg_params()
        total = sum(len(records) for records in targets)
        preview = total <= params["sync_limit"]
        lines = []
        for records in targets:
            for record in records:
                vals = {"res_model": record._name, "res_id": record.id, "name": record.display_name}
                if preview:
                    data = record._dt_bg_cutout(params)
                    vals.update(
                        image_before=record.image_1024,
                        image_after=data and base64.b64encode(data),
                        to_apply=bool(data),
                    )
                lines.append(fields.Command.create(vals))
        return self.create({"mode": "preview" if preview else "queue", "line_ids": lines})

    def action_apply(self):
        self.ensure_one()
        if self.mode == "queue":
            for line in self.line_ids:
                line._dt_record().bg_removal_state = "pending"
            self.env.ref("deltatech_image_optimize.ir_cron_dt_image_remove_background")._trigger()
            message = self.env._(
                "%(count)s images were queued; their background is removed by a scheduled action, in batches.",
                count=len(self.line_ids),
            )
        else:
            lines = self.line_ids.filtered(lambda line: line.to_apply and line.image_after)
            for line in lines:
                line._dt_record()._dt_bg_apply(base64.b64decode(line.image_after))
            message = self.env._("Background removed on %(count)s images.", count=len(lines))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": message, "type": "info", "next": {"type": "ir.actions.client", "tag": "soft_reload"}},
        }


class ImageBackgroundWizardLine(models.TransientModel):
    _name = "deltatech.image.background.wizard.line"
    _description = "Remove Image Background Line"

    wizard_id = fields.Many2one("deltatech.image.background.wizard", required=True, ondelete="cascade")
    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    name = fields.Char(string="Image")
    # în coloana tranzientei, nu în ir.attachment: dispare cu wizard-ul
    image_before = fields.Image(string="Before", attachment=False)
    image_after = fields.Image(string="After", attachment=False)
    to_apply = fields.Boolean(string="Apply")

    def _dt_record(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id)
