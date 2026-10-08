# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo import api, fields, models


class ImageWatermarkWizard(models.TransientModel):
    _name = "deltatech.image.watermark.wizard"
    _description = "Remove Image Watermark"

    mode = fields.Selection(
        [("preview", "Preview"), ("queue", "Queue")],
        required=True,
        default="preview",
        readonly=True,
    )
    profile_id = fields.Many2one("deltatech.image.watermark.profile", string="Watermark", readonly=True)
    preview = fields.Image(related="profile_id.preview", string="Detected Watermark")
    learned_count = fields.Integer(related="profile_id.image_count")
    line_ids = fields.One2many("deltatech.image.watermark.wizard.line", "wizard_id", string="Images")
    image_count = fields.Integer(compute="_compute_counts", string="Selected Images")
    failed_count = fields.Integer(compute="_compute_counts", string="Without Watermark")

    @api.depends("line_ids.image_after")
    def _compute_counts(self):
        for wizard in self:
            wizard.image_count = len(wizard.line_ids)
            wizard.failed_count = len(wizard.line_ids.filtered(lambda line: not line.image_after))

    @api.model
    def _dt_create_for(self, targets):
        """Învață watermark-ul din toate imaginile selectate, apoi previzualizare sau coadă.

        Până la ``wm_sync_limit`` imagini, watermark-ul se elimină acum, ca rezultatul să
        poată fi văzut înainte de a fi scris; peste limită, imaginile merg în coadă.
        """
        records = [record for group in targets for record in group]
        profile = self.env["deltatech.image.watermark.profile"]._dt_learn(records)
        preview = len(records) <= self.env["ir.attachment"]._dt_wm_params()["sync_limit"]
        lines = []
        for record in records:
            vals = {"res_model": record._name, "res_id": record.id, "name": record._dt_bg_line_name()}
            if preview:
                data, warning = record._dt_wm_clean(profile)
                vals.update(
                    image_before=record.image_1024,
                    image_after=data and base64.b64encode(data),
                    warning=warning,
                    to_apply=bool(data),
                )
            lines.append(fields.Command.create(vals))
        return self.create({"mode": "preview" if preview else "queue", "profile_id": profile.id, "line_ids": lines})

    def action_apply(self):
        self.ensure_one()
        if self.mode == "queue":
            for line in self.line_ids:
                line._dt_record().write({"wm_removal_state": "pending", "wm_profile_id": self.profile_id.id})
            self.env.ref("deltatech_image_optimize.ir_cron_dt_image_remove_watermark")._trigger()
            message = self.env._(
                "%(count)s images were queued; their watermark is removed by a scheduled action, in batches.",
                count=len(self.line_ids),
            )
        else:
            lines = self.line_ids.filtered(lambda line: line.to_apply and line.image_after)
            for line in lines:
                record = line._dt_record()
                record.wm_profile_id = self.profile_id
                record._dt_wm_apply(base64.b64decode(line.image_after))
            message = self.env._("Watermark removed on %(count)s images.", count=len(lines))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": message, "type": "info", "next": {"type": "ir.actions.client", "tag": "soft_reload"}},
        }


class ImageWatermarkWizardLine(models.TransientModel):
    _name = "deltatech.image.watermark.wizard.line"
    _description = "Remove Image Watermark Line"

    wizard_id = fields.Many2one("deltatech.image.watermark.wizard", required=True, ondelete="cascade")
    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    name = fields.Char(string="Image")
    # în coloana tranzientei, nu în ir.attachment: dispare cu wizard-ul
    image_before = fields.Image(string="Before", attachment=False)
    image_after = fields.Image(string="After", attachment=False)
    warning = fields.Char(readonly=True)
    to_apply = fields.Boolean(string="Apply")

    def _dt_record(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id)
