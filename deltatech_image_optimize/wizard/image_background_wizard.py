# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo import api, fields, models

# modelele rembg oferite în wizard; cel din parametrul de sistem se adaugă dacă lipsește
BG_MODELS = [
    ("isnet-general-use", "ISNet (fast)"),
    ("birefnet-general-lite", "BiRefNet lite"),
    ("birefnet-general", "BiRefNet (fine, slow)"),
    ("u2net", "U2Net"),
]


class ImageBackgroundWizard(models.TransientModel):
    _name = "deltatech.image.background.wizard"
    _description = "Remove Image Background"

    mode = fields.Selection(
        [("preview", "Preview"), ("queue", "Queue")],
        required=True,
        default="preview",
        readonly=True,
    )
    method = fields.Selection(
        [
            ("auto", "Automatic"),
            ("uniform", "Uniform background"),
            ("rembg", "AI model"),
        ],
        required=True,
        default="auto",
        help="Uniform background: the background is the color of the image border (a photo on white), "
        "no AI model; dark accessories next to the product are kept.\n"
        "AI model: for photos on a real background.\n"
        "Automatic: uniform background when the border has a single color, otherwise the AI model.",
    )
    bg_model = fields.Selection(selection="_selection_bg_model", string="AI Model")
    line_ids = fields.One2many("deltatech.image.background.wizard.line", "wizard_id", string="Images")
    image_count = fields.Integer(compute="_compute_counts", string="Selected Images")
    failed_count = fields.Integer(compute="_compute_counts", string="Not Cut Out")
    warning_count = fields.Integer(compute="_compute_counts", string="To Check")

    @api.model
    def _selection_bg_model(self):
        models_list = list(BG_MODELS)
        current = self.env["ir.attachment"]._dt_bg_params()["model"]
        if current not in dict(models_list):
            models_list.append((current, current))
        return models_list

    @api.depends("line_ids.image_after", "line_ids.warning")
    def _compute_counts(self):
        for wizard in self:
            wizard.image_count = len(wizard.line_ids)
            wizard.failed_count = len(wizard.line_ids.filtered(lambda line: not line.image_after))
            wizard.warning_count = len(wizard.line_ids.filtered(lambda line: line.image_after and line.warning))

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
                vals = {"res_model": record._name, "res_id": record.id, "name": record._dt_bg_line_name()}
                if preview:
                    vals.update(image_before=record.image_1024, **self._dt_preview_vals(record, params))
                lines.append(fields.Command.create(vals))
        return self.create(
            {
                "mode": "preview" if preview else "queue",
                "method": params["method"],
                "bg_model": params["model"],
                "line_ids": lines,
            }
        )

    @api.model
    def _dt_preview_vals(self, record, params):
        data, warning = record._dt_bg_cutout(params)
        return {
            "image_after": data and base64.b64encode(data),
            "warning": warning,
            # un rezultat suspect nu se aplică decât dacă utilizatorul îl bifează
            "to_apply": bool(data) and not warning,
        }

    def action_refresh(self):
        """Refă previzualizarea cu metoda și modelul alese în wizard."""
        self.ensure_one()
        params = dict(self.env["ir.attachment"]._dt_bg_params(), method=self.method)
        if self.bg_model:
            params["model"] = self.bg_model
        for line in self.line_ids:
            line.write(self._dt_preview_vals(line._dt_record(), params))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Remove Image Background"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {"dialog_size": "extra-large"},
        }

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
    warning = fields.Char(readonly=True)
    to_apply = fields.Boolean(string="Apply")

    def _dt_record(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id)
