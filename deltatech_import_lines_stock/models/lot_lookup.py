# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from collections import Counter


def find_lots(env, company, rows):
    """Return {(product id, lot name): lot} for the lots named in ``rows``, in one query."""
    names = {row["lot_name"] for row in rows if row.get("lot_name")}
    if not names:
        return {}
    product_ids = {row["product"].id for row in rows if row.get("lot_name")}
    lots = env["stock.lot"].search(
        [
            ("name", "in", list(names)),
            ("product_id", "in", list(product_ids)),
            ("company_id", "in", [company.id, False]),
        ]
    )
    return {(lot.product_id.id, lot.name): lot for lot in lots}


def duplicate_serials(rows):
    """Return the (product id, serial number) pairs that appear on more than one row."""
    keys = Counter(
        (row["product"].id, row["lot_name"])
        for row in rows
        if row.get("lot_name") and row["product"].tracking == "serial"
    )
    return {key for key, count in keys.items() if count > 1}
