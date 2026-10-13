# Copyright (C) 2020 NextERP Romania
# Copyright (C) 2020 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StorageSheet(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet"

    only_active = fields.Boolean(
        default=False,
        help="When set, the storage sheet only includes stock moves whose valuation is still active (not closed).",
    )

    def _get_active_move_filter(self):
        """Return an extra SQL predicate restricting the storage sheet to stock
        moves whose valuation is still active.

        In Odoo 19 valuation is stored on ``stock.move`` (the former
        ``stock.valuation.layer`` was removed); the ``active`` flag has been
        replaced by the custom, non-magic field ``l10n_ro_valuation_active``.
        When ``only_active`` is not set we return an empty string so the base
        report behaviour is preserved unchanged.
        """
        if self.only_active:
            return " AND sm.l10n_ro_valuation_active = true "
        return ""

    def _inject_active_filter(self, sql):
        """Append the active-valuation predicate to every ``stock_move``
        sub-query in the base SQL.

        The base report builds INSERT ... SELECT statements where each block
        filtering on ``stock_move sm`` ends with a location predicate. We anchor
        on those stable predicates and insert our filter right after them so it
        lands inside the correct WHERE clause without altering aggregation.
        """
        extra = self._get_active_move_filter()
        if not extra:
            return sql
        anchors = [
            "sm.location_dest_id in %(locations)s",
            "sm.location_id in %(locations)s",
        ]
        for anchor in anchors:
            sql = sql.replace(anchor, anchor + extra)
        return sql

    def _get_sql_select_sold_init(self):
        return self._inject_active_filter(super()._get_sql_select_sold_init())

    def _get_sql_select_sold_final(self):
        return self._inject_active_filter(super()._get_sql_select_sold_final())

    def _get_sql_select_in(self):
        return self._inject_active_filter(super()._get_sql_select_in())

    def _get_sql_select_out(self):
        return self._inject_active_filter(super()._get_sql_select_out())
