# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class UomUneceCode(models.Model):
    """UN/ECE code usable as the `unitCode` of an electronic document.

    Loaded from the nomenclature ANAF publishes with the SAF-T schema, which
    states the codes accepted for reporting along with their English name and an
    indicative Romanian translation:
    https://static.anaf.ro/static/10/Anaf/Informatii_R/RO_SAFT_SchemaDefCod_16.02.2026.xlsx

    A model rather than a selection field: the list holds over two thousand
    codes, ANAF republishes it periodically, and a consultant can add or correct
    an entry without a code change and a deployment.
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
    source = fields.Selection(
        [
            ("rec20", "Rec 20 - unit of measure"),
            ("rec21", "Rec 21 - packaging"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
        help="Which UN/ECE recommendation the code comes from, as stated by the ANAF nomenclature.",
    )
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint("unique(code)", "The UNECE code must be unique.")
    # Two to four characters: the recommendations use two or three, but the ANAF
    # nomenclature also carries XLTR (bulk litre of petroleum products). Note that
    # eTransport's own `CodUMType` accepts only two or three, so a four-character
    # code is reportable in SAF-T but not on a transport declaration.
    _code_format = models.Constraint(
        "check(code ~ '^[0-9A-Z]{2,4}$')",
        "The UNECE code must be 2 to 4 characters, digits or capital letters only.",
    )

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}" if record.name else record.code
