# ©  2015-2020 Terrabit
# See README.rst file on addons root folder for license details

import base64

from reportlab.graphics.barcode import createBarcodeDrawing

from odoo import api, fields, models


class ProductProductLabel(models.TransientModel):
    _name = "product.product.label"
    _description = "product.product.label"

    layout_id = fields.Many2one("ir.actions.report", string="Layout", required=True)
    label_lines = fields.One2many("product.product.label.line", "label_id", string="Labels")
    customer_id = fields.Many2one("res.partner", string="Customer")
    warehouse_id = fields.Many2one("stock.warehouse")
    use_location = fields.Boolean("Use ptw rules")
    location_id = fields.Many2one("stock.location")
    print_only_lots = fields.Boolean("Print lots only")
    # discount = fields.Float()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", [])
        model = self.env.context.get("active_model", False)
        warehouse_id = self.env.context.get("warehouse", False)
        if warehouse_id:
            res["warehouse_id"] = warehouse_id
        else:
            res["warehouse_id"] = self.env.ref("stock.warehouse0").id
        label_list = []
        product_list = {}
        if model == "product.template":
            label_list = self.get_product_template_lines(active_ids)

        if model == "product.product":
            label_list = self.get_product_lines(active_ids)

        if model == "sale.order":
            product_list = self.get_saleorder_lines(active_ids)

        if model == "stock.picking":
            product_list = self.get_picking_lines(active_ids)

        for item in product_list:
            label_list.append([0, 0, product_list[item]])

        res["label_lines"] = label_list
        return res

    @api.model
    def get_product_template_lines(self, active_ids, lots_only=False):
        label_list = []
        products = self.env["product.product"]
        product_tmpl = self.env["product.template"].browse(active_ids)
        for tmpl in product_tmpl:
            products |= tmpl.product_variant_ids
        for product in products:
            if not lots_only:
                label_list.append([0, 0, {"product_id": product.id, "quantity": 1}])
            else:
                quants = self.env["stock.quant"].search([("product_id", "=", product.id)])
                for quant in quants:
                    if quant.location_id.usage == "internal" and quant.lot_id:
                        label_list.append(
                            [
                                0,
                                0,
                                {
                                    "product_id": product.id,
                                    "quantity": quant.quantity,
                                    "lot": quant.lot_id.name,
                                },
                            ]
                        )
        return label_list

    @api.model
    def get_product_lines(self, active_ids, lots_only=False):
        label_list = []
        products = self.env["product.product"].browse(active_ids)
        for product in products:
            if not lots_only:
                label_list.append([0, 0, {"product_id": product.id, "quantity": 1}])
            else:
                quants = self.env["stock.quant"].search([("product_id", "=", product.id)])
                for quant in quants:
                    if quant.location_id.usage == "internal" and quant.lot_id:
                        label_list.append(
                            [
                                0,
                                0,
                                {
                                    "product_id": product.id,
                                    "quantity": quant.quantity,
                                    "lot": quant.lot_id.name,
                                },
                            ]
                        )
        return label_list

    @api.model
    def get_saleorder_lines(self, active_ids):
        sale_orders = self.env["sale.order"].browse(active_ids)
        product_list = {}
        products = self.env["product.product"]
        for sale_order in sale_orders:
            for line in sale_order.order_line:
                products |= line.product_id
                if line.product_id.id not in product_list:
                    product_list[line.product_id.id] = {
                        "product_id": line.product_id.id,
                        "quantity": line.product_uom_qty,
                    }
                else:
                    product_list[line.product_id.id]["quantity"] += line.product_uom_qty
        return product_list

    @api.model
    def get_picking_lines(self, active_ids):
        pickings = self.env["stock.picking"].browse(active_ids)
        product_list = {}
        for picking in pickings:
            for line in picking.move_line_ids:
                product_list[line.product_id.id] = {
                    "product_id": line.product_id.id,
                    "quantity": line.quantity,
                    "lot": line.lot_id.name if line.lot_id else "",
                }
        return product_list

    def print_labels(self):
        report = self.layout_id.report_action(self)
        return report

    @api.onchange("print_only_lots")
    def onchange_lots_option(self):
        if self.print_only_lots:
            self.label_lines.write({"label_id": False})
            self.label_lines.unlink()
            active_ids = self.env.context.get("active_ids", [])
            model = self.env.context.get("active_model", False)
            if model == "product.template":
                label_list = self.get_product_template_lines(active_ids, True)
                vals = []
                for label in label_list:
                    vals.append(
                        {
                            "product_id": label[2]["product_id"],
                            "quantity": 1,
                            "lot": label[2]["lot"],
                        }
                    )
                lines = self.env["product.product.label.line"].create(vals)
                self.write({"label_lines": [(4, line_id) for line_id in lines.ids]})
            if model == "product.product":
                label_list = self.get_product_lines(active_ids, True)
                vals = []
                for label in label_list:
                    vals.append(
                        {
                            "product_id": label[2]["product_id"],
                            "quantity": 1,
                            "lot": label[2]["lot"],
                        }
                    )
                lines = self.env["product.product.label.line"].create(vals)
                self.write({"label_lines": [(4, line_id) for line_id in lines.ids]})
            if model == "sale.order":
                return False

            if model == "stock.picking":
                return False


class ProductProductLabelLine(models.TransientModel):
    _name = "product.product.label.line"
    _description = "product.product.label.line"

    label_id = fields.Many2one(comodel_name="product.product.label", string="Product Label")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    quantity = fields.Integer(string="Label Qty", default=1)

    barcode_image = fields.Binary(string="Barcode Image", compute="_compute_barcode_image")

    lot = fields.Char()

    def _compute_barcode_image(self):
        for line in self:
            if line.product_id.barcode or line.product_id.default_code:
                if line.product_id.barcode:
                    barcode_image = createBarcodeDrawing(
                        "EAN13",
                        value=line.product_id.barcode,
                        width=200,
                        height=100,
                        format="svg",
                        humanReadable=True,
                    )

                    code = line.product_id.barcode
                else:
                    barcode_image = createBarcodeDrawing(
                        "Code128",
                        value=line.product_id.default_code or "no_barcode",
                        width=600,
                        height=100,
                        format="svg",
                        humanReadable=False,
                    )
                    code = line.product_id.default_code

                barcode_image.save(["svg"], fnRoot=code, outDir="/tmp")
                filename = f"/tmp/{code}.svg"
                with open(filename) as f:
                    barcode_image = f.read()

                barcode_image = base64.b64encode(barcode_image.encode())
                line.barcode_image = f"data:image/svg+xml;base64,{barcode_image.decode()}"

    def get_label_data(self):
        return {
            "label_id": self.label_id.id,
            "name": self.product_id.name,
            "code": self.product_id.default_code or False,
            "barcode": self.product_id.barcode or False,
            "lot": self.lot or False,
        }

    def get_location_line(self):
        self.ensure_one()
        self = self.sudo()
        location_line = False
        if self.label_id.warehouse_id and hasattr(self.product_id, "warehouse_loc_ids"):
            location_lines = self.product_id.warehouse_loc_ids.filtered(
                lambda p: p.warehouse_id == self.label_id.warehouse_id
            )
            if location_lines:
                location_line = location_lines[0]
        return location_line
