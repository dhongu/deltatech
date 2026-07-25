# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.tools import SQL


class StockPicking(models.Model):
    _inherit = "stock.picking"

    user_group_id = fields.Many2one("res.groups", string="User Group")

    def responsible_determination(self):
        """
        Balances user_id in pickings, depending on the products category's group(s)
        Can be called from button or from another custom function (e.g. action_assign)
        :return: nothing
        """
        pickings = self.filtered(lambda x: x.state == "assigned" and len(x.user_id) == 0)
        for picking in pickings:
            categ_ids = picking.move_line_ids.mapped("product_id.categ_id")
            categ_ids |= categ_ids.mapped("parent_id")
            categ_ids |= categ_ids.mapped("parent_id")
            categ_ids |= categ_ids.mapped("parent_id")
            user_group_ids = categ_ids.mapped("user_group_id")
            user_group_id = user_group_ids and user_group_ids[0] or False
            users = user_group_ids.mapped("user_ids")
            if users:
                # Flush pending writes so the raw SQL sees up-to-date user_id/state
                self.env["stock.picking"].flush_model(["user_id", "state"])
                self.env.cr.execute(
                    SQL(
                        """
                        SELECT u.id, count(p.id) AS count
                            FROM
                                res_users AS u
                                INNER JOIN stock_picking AS p ON p.user_id = u.id
                            WHERE p.state IN ('assigned') AND u.id IN %s
                            GROUP BY u.id
                            ORDER BY count(p.id)
                        """,
                        tuple(users.ids),
                    )
                )
                res = self.env.cr.fetchall()
                # user_id = False
                if res:
                    user_id = res[0][0]
                    user_ids = [x[0] for x in res]
                    for user in users:
                        if user.id not in user_ids:
                            user_id = user.id
                            break
                else:
                    user_id = users[0].id
                if user_id:
                    picking.write({"user_id": user_id})
                    self.env.cr.execute(
                        SQL(
                            """
                            UPDATE stock_picking
                                SET user_id = %s, user_group_id = %s
                                WHERE id = %s
                            """,
                            user_id,
                            user_group_id.id,
                            picking.id,
                        )
                    )
