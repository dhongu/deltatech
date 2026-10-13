from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sale_managers = env.ref("sales_team.group_sale_manager").user_ids
    commission_manager = env.ref("deltatech_sale_commission.group_commission_manager")
    commission_manager.write({"user_ids": [(4, user.id) for user in sale_managers]})
