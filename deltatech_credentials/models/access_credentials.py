# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccessCredentials(models.Model):
    _name = "access.credentials"
    _description = "Credentials"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    access_type = fields.Selection(
        [
            ("user", "User and password"),
            ("client", "Client_id and client_secret"),
            ("token", "Access token"),
        ],
        string="Access Type",
        default="user",
    )

    username = fields.Char(string="Username")
    password = fields.Char(string="Password")

    client_id = fields.Char(string="Client Id")
    client_secret = fields.Char(string="Client Secret / API key")

    access_token = fields.Char(string="Access Token")
