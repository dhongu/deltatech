# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    # lot_id = fields.Many2one("stock.production.lot", "Lot/Serial Number")

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.env.context.get("lot_ids", False):
            lots = self.env.context["lot_ids"]
            domain = [("move_line_ids.lot_id", "in", lots.ids)]
            moves = self.env["stock.move"].search(domain)
            if moves:
                args += [("stock_move_id", "in", moves.ids)]
        return super(StockValuationLayer, self)._search(args, offset, limit, order, count, access_rights_uid)

    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     if self.env.context.get("lot_ids", False):
    #         lots = self.env.context["lot_ids"]
    #         domain = [("move_line_ids.lot_id", "in", lots.ids)]
    #         moves = self.env["stock.move"].search(domain)
    #         if moves:
    #             args += [("stock_move_id", "in", moves.ids)]
    #
    #     return super(StockValuationLayer, self).search(args, offset, limit=limit, order=order, count=count)

    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.context.get("lot_ids", False):
            lots = self.env.context["lot_ids"]
            local_domain = [("move_line_ids.lot_id", "in", lots.ids)]
            moves = self.env["stock.move"].search(local_domain)
            if moves:
                domain += [("stock_move_id", "in", moves.ids)]
        return super(StockValuationLayer, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
