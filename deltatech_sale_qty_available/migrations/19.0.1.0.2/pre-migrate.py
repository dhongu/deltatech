from odoo.tools import SQL


def migrate(cr, version):
    # Add is_ready column if it doesn't exist yet (before ORM runs)
    cr.execute(
        SQL("""
        ALTER TABLE sale_order
        ADD COLUMN IF NOT EXISTS is_ready boolean DEFAULT false
    """)
    )
