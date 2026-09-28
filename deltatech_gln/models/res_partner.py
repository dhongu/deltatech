# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from stdnum import ean

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools import SQL

GLN_KEY = "EAN_GLN"
_LIKE_OPERATORS = ("like", "ilike", "=like", "=ilike")


class Partner(models.Model):
    _inherit = "res.partner"

    # Since 20.0 the GLN is a standard partner identifier, kept by `base` in
    # `additional_identifiers["EAN_GLN"]` (the same value `account` exposes as
    # `global_location_number`). `gln` stays as the public API of this module
    # (read / write / search), but it is only a proxy on the standard storage.
    gln = fields.Char(
        string="Global Location Number",
        help="GLN - kept in the standard partner identifiers (EAN/GLN).",
        compute="_compute_gln",
        inverse="_inverse_gln",
        search="_search_gln",
    )

    @api.depends("additional_identifiers")
    def _compute_gln(self):
        for partner in self:
            partner.gln = partner._get_additional_identifier(GLN_KEY) or False

    def _inverse_gln(self):
        for partner in self:
            partner._set_additional_identifier(GLN_KEY, partner.gln)

    def _search_gln(self, operator, value):
        if operator == "in":
            # COALESCE: never NULL, so that the negation (`!=`, `not in`) keeps
            # the partners without a GLN, as for a stored Char field
            values = tuple({ean.compact(v) if v else "" for v in value}) or ("",)

            def to_sql(table):
                gln = SQL("COALESCE(%s ->> %s, '')", table.additional_identifiers, GLN_KEY)
                return SQL("%s IN %s", gln, values) if value else SQL("FALSE")

            return Domain.custom(to_sql=to_sql)

        if operator in _LIKE_OPERATORS:
            sql_operator = SQL(operator.lstrip("=").upper())
            pattern = value if operator.startswith("=") else f"%{value}%"

            def to_sql(table):
                gln = SQL("COALESCE(%s ->> %s, '')", table.additional_identifiers, GLN_KEY)
                return SQL("%s %s %s", gln, sql_operator, pattern)

            return Domain.custom(to_sql=to_sql)

        return NotImplemented
