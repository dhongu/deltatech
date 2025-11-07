from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_team_from_values(self, values):
        group = values.get("group_id")
        if group:
            return group.team_id.id

        return False

    def _make_po_get_domain(self, company_id, values, partner):
        # Extend the standard domain so that POs are split per Sales Team when provided
        domain = super()._make_po_get_domain(company_id, values, partner)
        team_id = self._get_team_from_values(values)
        if team_id:
            domain += (("team_id", "=", team_id),)
        return domain

    def _prepare_purchase_order(self, company_id, origins, values_list):
        # values_list is a list of values (one per procurement) for the same PO domain
        vals = super()._prepare_purchase_order(company_id, origins, values_list)
        # Try to get team_id from the first values dict
        team_id = False
        if values_list:
            team_id = self._get_team_from_values(values_list[0])
        if team_id:
            vals["team_id"] = team_id
        return vals

    # def _make_po(self, product_id, procurement_values, po_company_id, origin=None, values=None):
    #     # Call standard logic to get/create the PO
    #     po = super()._make_po(product_id, procurement_values, po_company_id, origin, values)
    #
    #     # Assign Sales Team on PO if provided or derivable from procurement
    #     team_id = self._get_team_from_values(procurement_values)
    #     if team_id and po.team_id.id != team_id:
    #         po.team_id = team_id
    #
    #     return po
