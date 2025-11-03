from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from .transport_utils import (
    ensure_manifest_has_data,
    git_commit_push,
    map_xmlid,
    write_to_module_data_folder,
)


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
        help="Select the fields to export. Only fields from the selected model are available.",
    )

    domain = fields.Char(string="Domain", help="Expression list, e.g. [('company_id','=',1)]")
    last_export = fields.Datetime(string="Last Export")
    repo_id = fields.Many2one("transport.repo", string="Git Repository")

    @api.onchange("model_id")
    def _onchange_model_id(self):
        # Clear selected fields when model changes
        self.field_ids = [(5, 0, 0)]

    @api.constrains("field_ids", "model_id")
    def _check_fields_match_model(self):
        for rec in self:
            if rec.field_ids and any(f.model_id.id != rec.model_id.id for f in rec.field_ids):
                raise ValidationError("Toate câmpurile selectate trebuie să aparțină modelului ales.")

    def action_export_csv(self):
        # Allow multi-record execution (from list server action)
        if len(self) > 1:
            count = 0
            for cfg in self:
                cfg._export_one()
                count += 1
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Exporturi realizate",
                    "message": f"Au fost executate {count} exporturi.",
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            return self._export_one()

    def _export_one(self):
        self.ensure_one()
        if not self.repo_id or not self.repo_id.module_name:
            raise UserError("Configurația nu are setat un Repository cu numele modulului țintă (module_name).")
        model = self.env[self.model_id.model]
        domain = safe_eval(self.domain or "[]")
        records = model.search(domain)
        if not records:
            raise UserError("Nu există înregistrări pentru domeniul dat.")

        # Field selection via Many2many is mandatory
        # Ensure we don't duplicate the 'id' column; it will be generated as External ID
        field_names = [n for n in self.field_ids.mapped("name") if n != "id"]
        if not field_names:
            raise UserError("Nu ai specificat câmpurile pentru export.")

        import csv
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        # First column must be External ID (Odoo export convention uses header 'id')
        header = ["id"] + field_names
        writer.writerow(header)

        # Precompute external ids mapping for efficiency
        ext_map = records.get_external_id()

        for rec in records:
            # External ID or fallback to model,id
            ext_id = ext_map.get(rec.id) or f"{rec._name},{rec.id}"
            row = [ext_id]
            for f in field_names:
                if not hasattr(rec, f):
                    row.append("")
                    continue
                val = getattr(rec, f)
                # Map relations to XMLID
                val = map_xmlid(val)
                row.append(val)
            writer.writerow(row)

        csv_data = buf.getvalue()

        # Attach CSV to chatter for easy access
        target_filename = f"{self.model_id.model}.csv"

        attachment = self.env["ir.attachment"].create(
            {
                "name": target_filename,
                "res_model": self._name,
                "res_id": self.id,
                "type": "binary",
                "mimetype": "text/csv",
                "raw": csv_data.encode("utf-8"),
            }
        )
        # Post a message with the attachment
        self.message_post(
            body=f"Export CSV generat pentru modelul {self.model_id.model}.", attachment_ids=[attachment.id]
        )

        # Write under <module>/data and ensure manifest reference
        csv_abs_path, rel_manifest_path = write_to_module_data_folder(
            csv_data, self.repo_id.module_name, target_filename
        )
        manifest_path, changed = ensure_manifest_has_data(self.repo_id.module_name, rel_manifest_path)

        # Save CSV in module folder and push to Git if repo configured
        if self.repo_id:
            try:
                files_to_commit = [csv_abs_path]
                # if manifest updated, include it too
                if changed:
                    files_to_commit.append(manifest_path)
                git_commit_push(
                    files_to_commit, f"Export {self.model_id.model} via deltatech_transport_change", self.repo_id
                )
            except Exception as e:
                # Do not block export; inform via chatter
                self.message_post(body=f"[Git] Commit/Push a eșuat: {e}")

        self.write({"last_export": fields.Datetime.now()})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Export realizat",
                "message": f"Au fost exportate {len(records)} înregistrări din {self.model_id.model}. Fișierul este atașat în chatter și scris în modul (data).",
                "type": "success",
                "sticky": False,
            },
        }
