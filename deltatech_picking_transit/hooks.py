# hooks.py

from odoo import _


def post_init_hook(env):
    """Set up the two-step transit configuration on a fresh install.

    Runs only at install time (never on module update), so databases that
    already use this module are left untouched. For every company it creates a
    dedicated transit stock location and, on each of the company warehouses, a
    two-step delivery operation type (with automatic second transfer) and a
    two-step reception operation type, wired to the warehouse main stock
    location and the transit location.
    """
    for company in env["res.company"].search([]):
        _setup_company_two_step_transit(env, company)


def _setup_company_two_step_transit(env, company):
    Location = env["stock.location"].with_company(company)
    PickingType = env["stock.picking.type"].with_company(company)

    parent_location = env.ref("stock.stock_location_locations", raise_if_not_found=False)
    transit_location = Location.create(
        {
            "name": _("2-Step Transit"),
            "usage": "transit",
            "location_id": parent_location.id if parent_location else False,
            "company_id": company.id,
        }
    )

    warehouses = env["stock.warehouse"].search([("company_id", "=", company.id)])
    for warehouse in warehouses:
        stock_location = warehouse.lot_stock_id

        # Two-step delivery: warehouse stock -> transit, with automatic
        # creation of the second (reception) transfer on validation.
        if not _has_two_step_type(PickingType, warehouse, "delivery"):
            PickingType.create(
                {
                    "name": _("2-Step Delivery"),
                    "code": "internal",
                    "sequence_code": "2SD",
                    "warehouse_id": warehouse.id,
                    "company_id": company.id,
                    "default_location_src_id": stock_location.id,
                    "default_location_dest_id": transit_location.id,
                    "two_step_transfer_use": "delivery",
                    "auto_second_transfer": True,
                }
            )

        # Two-step reception: transit -> warehouse stock.
        if not _has_two_step_type(PickingType, warehouse, "reception"):
            PickingType.create(
                {
                    "name": _("2-Step Reception"),
                    "code": "internal",
                    "sequence_code": "2SR",
                    "warehouse_id": warehouse.id,
                    "company_id": company.id,
                    "default_location_src_id": transit_location.id,
                    "default_location_dest_id": stock_location.id,
                    "two_step_transfer_use": "reception",
                }
            )


def _has_two_step_type(PickingType, warehouse, use):
    return bool(
        PickingType.search(
            [
                ("warehouse_id", "=", warehouse.id),
                ("code", "=", "internal"),
                ("two_step_transfer_use", "=", use),
            ],
            limit=1,
        )
    )
