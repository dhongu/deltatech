# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class UomUneceCode(models.Model):
    """UN/ECE code usable as the `unitCode` of an electronic document.

    A model rather than a selection field: the published lists hold well over a
    thousand codes, new ones are added by UN/CEFACT, and which ones a customer
    needs depends on their trade. A consultant can add the missing code without
    a code change and a deployment.
    """

    _name = "uom.unece.code"
    _description = "UNECE Unit of Measure Code"
    _order = "code"

    code = fields.Char(
        required=True,
        index=True,
        help="Code sent as the unitCode attribute, e.g. KGM for kilogram.",
    )
    name = fields.Char(required=True, translate=True, help="Meaning of the code in the UN/ECE list.")
    category = fields.Selection(
        [
            ("mass", "Mass"),
            ("volume", "Volume"),
            ("length", "Length"),
            ("area", "Area"),
            ("count", "Count"),
            ("packaging", "Packaging"),
            ("time", "Time"),
            ("energy", "Energy"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint("unique(code)", "The UNECE code must be unique.")
    # The receiving schemas accept two or three upper-case alphanumerics; ANAF's
    # eTransport `CodUMType` uses exactly this pattern.
    _code_format = models.Constraint(
        "check(code ~ '^[0-9A-Z]{2,3}$')",
        "The UNECE code must be 2 or 3 characters, digits or capital letters only.",
    )

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}" if record.name else record.code
