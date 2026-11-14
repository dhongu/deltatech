# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    # the roles are added by the modules that use them, with `selection_add`
    attribute_role = fields.Selection(
        [],
        string="Role",
        copy=False,
        help="What this attribute stands for in the business flows of the "
        "installed modules. Code finds the attribute by its role, so the attribute "
        "can be renamed or translated freely. A role can be held by one attribute "
        "only.",
    )

    _attribute_role_uniq = models.Constraint(
        "UNIQUE(attribute_role)",
        "A role can be held by one attribute only.",
    )

    @api.model
    def _get_attribute_by_role(self, role):
        """The attribute holding `role`, archived ones included, or an empty
        recordset."""
        return self.with_context(active_test=False).search([("attribute_role", "=", role)], limit=1)
