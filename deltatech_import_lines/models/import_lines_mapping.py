# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

TARGETS = [
    ("product", "Product"),
    ("quantity", "Quantity"),
    ("price_unit", "Unit Price"),
    ("discount", "Discount (%)"),
    ("uom", "Unit of Measure"),
    ("lot", "Lot/Serial Number"),
    ("description", "Description"),
]

MATCH_KEYS = [
    ("default_code", "Internal Reference"),
    ("barcode", "Barcode"),
    ("name", "Product Name"),
]


class ImportLinesMapping(models.Model):
    _name = "import.lines.mapping"
    _description = "Import Lines Column Mapping"
    _order = "res_model, partner_id, name"
    _check_company_auto = True

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    res_model = fields.Selection(selection="_selection_res_model", string="Document Type", required=True)
    partner_id = fields.Many2one(
        "res.partner",
        check_company=True,
        domain="[('parent_id', '=', False)]",
        help="When set, the mapping is proposed first for the documents of this partner.",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    has_header = fields.Boolean("Header Row", default=True)
    separator = fields.Char(help="Column separator for CSV and TXT files. Leave empty to detect it.")
    match_by = fields.Selection(MATCH_KEYS, string="Match Product By", required=True, default="default_code")
    column_ids = fields.One2many("import.lines.mapping.column", "mapping_id", string="Columns", copy=True)

    @api.model
    def _selection_res_model(self):
        names = [name for name in self.env.registry["import.lines.mixin"]._inherit_children if name in self.env]
        labels = [(name, self.env["ir.model"]._get(name).name or self.env[name]._description) for name in names]
        return sorted(labels, key=lambda item: item[1])

    @api.model
    def _find_for(self, res_model, partner):
        """Return the mapping of the partner for the document type, or else the generic one."""
        company = self.env.company
        domain = [("res_model", "=", res_model), ("company_id", "in", [company.id, False])]
        mapping = self.browse()
        if partner:
            mapping = self.search(domain + [("partner_id", "=", partner.commercial_partner_id.id)], limit=1)
        return mapping or self.search(domain + [("partner_id", "=", False)], limit=1)


class ImportLinesMappingColumn(models.Model):
    _name = "import.lines.mapping.column"
    _description = "Import Lines Mapping Column"
    _order = "mapping_id, column_index"

    mapping_id = fields.Many2one("import.lines.mapping", required=True, ondelete="cascade", index=True)
    column_index = fields.Integer("Column", help="Column position in the file, starting with 1.")
    header = fields.Char(help="Column title in the header row. Used before the position when the file has a header.")
    target = fields.Selection(TARGETS, required=True)
