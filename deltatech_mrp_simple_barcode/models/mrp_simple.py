from odoo import models


class MRPSimple(models.Model):
    _name = "mrp.simple"
    _inherit = ["mrp.simple", "barcodes.barcode_events_mixin"]

    def _add_product(self, product, qty=1.0):
        existing_line = self.product_out_ids.filtered(lambda r: r.product_id.id == product.id)
        if existing_line:
            existing_line.quantity += qty
            message = self.env._("The %(product_name)s product quantity was set to %(product_qty)s") % {
                "product_name": product.name,
                "product_qty": existing_line.quantity,
            }
            res = {"warning": {"title": self.env._("Info"), "type": "notification", "message": message}}
        else:
            vals = {
                "mrp_simple_id": self.id,
                "product_id": product.id,
                "quantity": qty,
            }
            self.product_out_ids.new(vals)
            existing_line = self.product_out_ids.filtered(lambda r: r.product_id.id == product.id)
            existing_line.onchange_product_id()
            message = self.env._("The %s product was added") % (product.name)
            res = {"warning": {"title": self.env._("Info"), "type": "notification", "message": message}}
        return res

    def on_barcode_scanned(self, barcode):
        if self.state != "draft":
            message = self.env._("Status does not allow scanning")
            res = {"warning": {"title": self.env._("Error"), "type": "danger", "message": message}}

            return res

        product = self.env["product.product"].search([("barcode", "=", barcode)])
        if not product:
            product = self.env["product.product"].search([("default_code", "=", barcode)])
        if product:
            res = self._add_product(product)
        else:
            message = self.env._("There is no product with barcode or internal reference %s") % barcode
            res = {"warning": {"title": self.env._("Error"), "type": "danger", "message": message}}

        return res
