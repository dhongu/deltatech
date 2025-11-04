import csv
import io
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from .transport_utils import (
    _bump_manifest_version_inplace,
    map_xmlid,
)

_logger = logging.getLogger(__name__)


class TransportConfig(models.Model):
    _name = "transport.config"
    _description = "Transport Configuration Export"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    model_id = fields.Many2one("ir.model", string="Model")
    model_name = fields.Char(related="model_id.model", readonly=True)
    field_ids = fields.Many2many(
        "ir.model.fields",
        string="Fields",
        domain="[('model_id', '=', model_id)]",
        help="The fields to export. Only fields from the selected model are available.",
    )

    domain = fields.Char(string="Domain", help="Expression list, e.g. [('company_id','=',1)]")
    last_export = fields.Datetime(string="Last Export")
    repo_id = fields.Many2one("transport.repo", string="Git Repository")

    @api.onchange("model_id")
    def _onchange_model_id(self):
        # Clear selected fields when model changes
        self.field_ids = [(5, 0, 0)]
        self.name = self.model_id.name if self.model_id else ""

    @api.constrains("field_ids", "model_id")
    def _check_fields_match_model(self):
        for rec in self:
            if rec.field_ids and any(f.model_id.id != rec.model_id.id for f in rec.field_ids):
                raise ValidationError("All selected fields must belong to the chosen model.")

    def action_export_csv(self):
        # Batch flow (also handles single-record): group by repo (url+branch) and process with a single clone per group
        if not self:
            return True

        # Validate all have repo and module
        for cfg in self:
            if not cfg.repo_id or not cfg.repo_id.module_name:
                raise UserError("All selected configurations must have a Repository set with a module_name.")

        repos = self.mapped("repo_id")

        total_exports = 0
        for repo in repos:
            # Enforce HTTPS + token
            cfgs = self.filtered(lambda c: c.repo_id == repo)
            branch = repo.repo_branch

            # Clone once
            try:
                # one clone per group using the group's repo record
                tmp_root, repo_obj = repo.clone_to_temp()
            except Exception as e:
                for c in cfgs:
                    c.message_post(body=f"[Git] Repository clone failed: {e}")
                continue

            # Prepare tracking for written files in this group
            written_files = []
            manifest_path = None

            try:
                for cfg in cfgs:
                    csv_data, filename = cfg._generate_csv_data()
                    # Attach per-config CSV
                    cfg._attach_csv_in_chatter(filename, csv_data)
                    # Write into clone under module_name/data via repo method
                    csv_abs, manifest_abs, changed, rel = cfg.repo_id.write_csv_and_update_manifest(
                        repo_root=tmp_root, filename=filename, data_content=csv_data
                    )
                    manifest_path = manifest_abs
                    written_files.append(rel)
                    total_exports += 1

                # Bump manifest version once
                if manifest_path:
                    _bump_manifest_version_inplace(manifest_path)

                # Commit and push once
                commit_msg = f"Transport export: {', '.join(written_files)}"
                try:
                    repo.commit_and_push(repo_obj, commit_msg)
                    # Post summary message
                    for cfg in cfgs:
                        cfg.message_post(body=f"[Git] Commit & push succeeded on {branch}: {', '.join(written_files)}")
                except Exception as e:
                    for cfg in cfgs:
                        cfg.message_post(body=f"[Git] Push failed on {branch}: {e}")
            finally:
                # Cleanup temp clone
                try:
                    import shutil

                    shutil.rmtree(tmp_root, ignore_errors=True)
                except Exception:
                    pass

        for cfg in self:
            cfg.write({"last_export": fields.Datetime.now()})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Exports completed",
                "message": f"Exported {total_exports} dataset(s).",
                "type": "success",
                "sticky": False,
            },
        }

    def _generate_csv_data(self):
        self.ensure_one()
        model = self.env[self.model_id.model]
        domain = safe_eval(self.domain or "[]")
        records = model.search(domain)
        if not records:
            raise UserError("There are no records for the given domain.")
        field_names = [n for n in self.field_ids.mapped("name") if n != "id"]
        if not field_names:
            raise UserError("You have not specified fields to export.")
        buf = io.StringIO()
        writer = csv.writer(buf)
        header = ["id"] + field_names
        writer.writerow(header)
        ext_map = records.get_external_id()
        for rec in records:
            ext_id = ext_map.get(rec.id) or f"{rec._name},{rec.id}"
            row = [ext_id]
            for f in field_names:
                val = getattr(rec, f, "")
                row.append(map_xmlid(val))
            writer.writerow(row)
        csv_data = buf.getvalue()
        filename = f"{self.model_id.model}.csv"
        return csv_data, filename

    def _attach_csv_in_chatter(self, filename, csv_data):
        att = self.env["ir.attachment"].create(
            {
                "name": filename,
                "res_model": self._name,
                "res_id": self.id,
                "type": "binary",
                "mimetype": "text/csv",
                "raw": csv_data.encode("utf-8"),
            }
        )
        self.message_post(body=f"CSV export generated for model {self.model_id.model}.", attachment_ids=[att.id])
