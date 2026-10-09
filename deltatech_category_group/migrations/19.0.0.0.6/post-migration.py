from odoo.tools import SQL


def migrate(cr, version):
    """CATEGORYGROUP-001: remove the implied links created by the old security.xml.

    The group "Manage category groups" used to imply ``base.user_root`` and
    ``base.user_admin``, i.e. res.users IDs stored as res.groups IDs in
    ``res_groups_implied_rel``. Only these two links of this group are removed.
    """
    cr.execute(
        SQL(
            """
            DELETE FROM res_groups_implied_rel rel
             USING ir_model_data grp, ir_model_data usr
             WHERE grp.module = 'deltatech_category_group'
               AND grp.name = 'category_group_manager'
               AND grp.model = 'res.groups'
               AND rel.gid = grp.res_id
               AND usr.module = 'base'
               AND usr.name IN ('user_root', 'user_admin')
               AND usr.model = 'res.users'
               AND rel.hid = usr.res_id
            """
        )
    )
