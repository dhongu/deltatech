# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_confirm(self):
        res = super().action_confirm()
        self.responsible_determination()
        return res

    def action_assign(self):
        res = super().action_assign()
        self.responsible_determination()
        return res

    def responsible_determination(self):
        pickings = self.filtered(lambda x: x.state == "assigned" and x.user_id is False)
        for picking in pickings:
            categ_ids = picking.move_lines.mapped("product_id.categ_id")
            categ_ids |= categ_ids.mapped("parent_id")
            user_group_ids = categ_ids.mapped("user_group_id")
            users = user_group_ids.mapped("users")
            if users:
                SQL = """
                    select u.id, count(p.id) as count
                        from
                            res_users as u
                            inner join stock_picking as p on p.user_id = u.id
                        where state in ('assigned')  and u.id in %s
                        group by u.id
                        order by count(p.id)
                """
                self.env.cr.execute(SQL, (tuple(users.ids),))
                res = self.env.cr.fetchall()
                user_id = False
                if res:
                    user_id = res[0][0]
                    user_ids = [x[0] for x in res]
                    for user in users:
                        if user.id not in user_ids:
                            user_id = user.id
                            break
                if user_id:
                    picking.write({"user_id": user_id})
                    SQL = """
                    update stock_picking
                        set user_id = %s
                        where id = %s
                    """
                    self.env.cr.execute(SQL, (user_id, picking.id))
