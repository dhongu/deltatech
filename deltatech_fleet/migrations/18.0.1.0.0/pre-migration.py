# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tools import SQL


def migrate(cr, version):
    """Up to 17.0 the module replaced fleet.vehicle.category_id (standard comodel
    fleet.vehicle.model.category) with a link to fleet.vehicle.category.
    The values move to vehicle_category_id and category_id is left to the
    standard fleet module."""
    if not version:
        return
    cr.execute(
        """
        SELECT 1
          FROM pg_constraint c
          JOIN pg_class t ON t.oid = c.conrelid
          JOIN pg_class r ON r.oid = c.confrelid
          JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY (c.conkey)
         WHERE c.contype = 'f'
           AND t.relname = 'fleet_vehicle'
           AND a.attname = 'category_id'
           AND r.relname = 'fleet_vehicle_category'
        """
    )
    if not cr.fetchone():
        return
    cr.execute("ALTER TABLE fleet_vehicle ADD COLUMN IF NOT EXISTS vehicle_category_id integer")
    cr.execute("UPDATE fleet_vehicle SET vehicle_category_id = category_id, category_id = NULL")
    cr.execute(
        """
        SELECT c.conname
          FROM pg_constraint c
          JOIN pg_class t ON t.oid = c.conrelid
          JOIN pg_class r ON r.oid = c.confrelid
         WHERE c.contype = 'f' AND t.relname = 'fleet_vehicle' AND r.relname = 'fleet_vehicle_category'
        """
    )
    for (name,) in cr.fetchall():
        cr.execute(SQL("ALTER TABLE fleet_vehicle DROP CONSTRAINT %s", SQL.identifier(name)))
