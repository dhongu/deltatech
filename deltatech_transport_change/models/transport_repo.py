from odoo import fields, models


class TransportRepo(models.Model):
    _name = "transport.repo"
    _description = "Transport Repo Configuration"

    name = fields.Char(required=True, string="Repo Name")
    module_name = fields.Char(required=True, string="Client Module")
    repo_url = fields.Char(required=True, string="Git URL")
    repo_branch = fields.Char(required=True, string="Branch")
    credential_type = fields.Selection([("ssh", "SSH Key"), ("https", "HTTPS")], default="ssh")
    ssh_key = fields.Binary(string="SSH Private Key")
    username = fields.Char(string="Git Username")
    password = fields.Char(string="Git Token / Password")
    repo_local_path = fields.Char(string="Local Path")
