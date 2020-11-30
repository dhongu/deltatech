# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class CommissionUpdatePurchasePrice(models.TransientModel):
    _name = "commission.update.purchase.price"
    _description = "Update purchase price"

    for_all = fields.Boolean(string="For all lines")
    price_from_doc = fields.Boolean(string="Price from delivery", default=True)

    invoice_line_ids = fields.Many2many(
        "sale.margin.report",
        "commission_update_purchase_price_inv_rel",
        "compute_id",
        "invoice_line_id",
        string="Account invoice line",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(CommissionUpdatePurchasePrice, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("id", "in", active_ids)]
        else:
            domain = [("state", "=", "paid"), ("commission", "=", 0.0)]
        res = self.env["sale.margin.report"].search(domain)
        defaults["invoice_line_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_compute(self):

        if self.for_all:
            lines = self.env["sale.margin.report"].search([])
        else:
            lines = self.invoice_line_ids

        for line in lines:
            invoice_line = self.env["account.invoice.line"].browse(line.id)
            purchase_price = 0.0
            pickings = self.env["stock.picking"]
            if self.price_from_doc:
                for sale_line in invoice_line.sale_line_ids:
                    pickings |= sale_line.order_id.picking_ids

                # sont doar livrari ?
                moves = self.env["stock.move"].search(
                    [("picking_id", "in", pickings.ids), ("product_id", "=", invoice_line.product_id.id)]
                )

                price_unit_list = moves.mapped("price_unit")  # preturile din livare sunt negative
                if price_unit_list:
                    purchase_price = abs(sum(price_unit_list) / float(len(price_unit_list)))

                if not purchase_price:
                    if invoice_line.product_id:
                        if invoice_line.product_id.standard_price > 0:
                            purchase_price = invoice_line.product_id.standard_price
            else:
                if invoice_line.product_id:
                    if invoice_line.product_id.standard_price > 0:
                        purchase_price = invoice_line.product_id.standard_price

            if purchase_price:
                invoice_line.write({"purchase_price": purchase_price})
        return True
