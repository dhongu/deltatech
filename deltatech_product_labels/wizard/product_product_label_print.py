# ©  2015-2020 Terrabit
# See README.rst file on addons root folder for license details

import base64

from reportlab.graphics.barcode import createBarcodeDrawing

from odoo import _, api, fields, models
from odoo.osv import expression


class ProductProductLabel(models.TransientModel):
    _name = "product.product.label"
    _description = "product.product.label"
    _inherit = ["barcodes.barcode_events_mixin"]

    layout_id = fields.Many2one("ir.actions.report", string="Layout", required=True)
    label_lines = fields.One2many("product.product.label.line", "label_id", string="Labels")
    customer_id = fields.Many2one("res.partner", string="Customer")
    warehouse_id = fields.Many2one("stock.warehouse")
    use_location = fields.Boolean("Use ptw rules")
    location_id = fields.Many2one("stock.location")
    print_only_lots = fields.Boolean("Print lots only")
    pricelist_id = fields.Many2one("product.pricelist", string="Price List")
    can_generate_lots = fields.Boolean(compute="_compute_can_generate_lots")
    auto_generate_lots = fields.Boolean()

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
            label_list = self.get_picking_lines(active_ids)

        if model == "stock.lot":
            label_list = self.get_lot_lines(active_ids)

        if model == "stock.quant":
            label_list = self.get_quant_lines(active_ids)

        for item in product_list:
            label_list.append([0, 0, product_list[item]])

        res["label_lines"] = label_list
        return res

    @api.depends("label_lines")
    def _compute_can_generate_lots(self):
        model = self.env.context.get("active_model", False)
        for label in self:
            if model != "stock.picking":
                label.can_generate_lots = False
            else:
                label.can_generate_lots = True
                active_ids = self.env.context.get("active_ids", [])
                pickings = self.env["stock.picking"].browse(active_ids)
                for picking in pickings:
                    picking_type = picking.picking_type_id
                    if picking_type.use_create_lots or picking_type.use_existing_lots:
                        if picking_type.code not in ["incoming", "dropship"]:
                            label.can_generate_lots = False

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
                domain = [("product_id", "=", product.id)]
                if self.warehouse_id:
                    location_id = self.warehouse_id.lot_stock_id
                    domain = expression.AND([[("location_id", "child_of", location_id.id)], domain])
                quants = self.env["stock.quant"].search(domain)
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
        product_list = []
        for picking in pickings:
            for line in picking.move_line_ids:
                product_list.append(
                    [
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "quantity": line.quantity,
                            "lot": line.lot_id.name if line.lot_id else line.lot_name,
                        },
                    ]
                )
        return product_list

    @api.model
    def get_lot_lines(self, active_ids):
        lots = self.env["stock.lot"].browse(active_ids)
        product_list = []
        for lot in lots:
            product_list.append(
                [
                    0,
                    0,
                    {
                        "product_id": lot.product_id.id,
                        "quantity": lot.product_qty or 1,
                        "lot": lot.name,
                    },
                ]
            )
        return product_list

    @api.model
    def get_quant_lines(self, active_ids):
        quants = self.env["stock.quant"].browse(active_ids)
        product_list = []
        for quant in quants:
            product_list.append(
                [
                    0,
                    0,
                    {
                        "product_id": quant.product_id.id,
                        "quantity": quant.quantity or 1,
                        "lot": quant.lot_id.name if quant.lot_id else "",
                    },
                ]
            )
        return product_list

    def generate_lots(self):
        active_ids = self.env.context.get("active_ids", [])
        pickings = self.env["stock.picking"].browse(active_ids)
        for picking in pickings:
            picking_type = picking.picking_type_id
            if picking_type.use_create_lots or picking_type.use_existing_lots:
                if picking_type.code in ["incoming", "dropship"]:
                    for line in picking.move_line_ids:
                        if line.product_id.tracking == "lot" and not line.lot_name:
                            line.lot_name = self.env["ir.sequence"].next_by_code("stock.lot.serial")
        self.label_lines.unlink()
        label_list = self.get_picking_lines(active_ids)
        for label in label_list:
            label[2]["label_id"] = self.id
            self.label_lines.create(label[2])

    def print_labels(self):
        if self.auto_generate_lots:
            self.generate_lots()
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
                            "quantity": label[2]["quantity"],
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

    @api.onchange("pricelist_id")
    def onchange_pricelist(self):
        for label in self:
            label.label_lines._compute_price()

    # barcode functions
    def on_barcode_scanned(self, barcode):
        product = self.env["product.product"].search([("barcode", "=", barcode)])

        if not product:
            product = self.env["product.product"].search([("default_code", "=", barcode)])
        if product:
            res = self._add_product(product)
        else:
            message = _("There is no product with barcode %s") % barcode
            res = {"warning": {"title": _("Error"), "type": "danger", "message": message}}

        return res

    def _add_product(self, product, qty=1.0):
        label_line = self.label_lines.filtered(lambda r: r.product_id.id == product.id)
        if label_line:
            label_line.quantity += qty
            message = _("The %(product_name)s product quantity was set to %(product_qty)s") % {
                "product_name": product.name,
                "product_qty": label_line.quantity,
            }
            res = {"warning": {"title": _("Info"), "type": "success", "message": message}}
        else:
            self.label_lines = [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "quantity": 1,
                    },
                )
            ]
            message = _("The %(product_name)s product quantity was set to %(product_qty)s") % {
                "product_name": product.name,
                "product_qty": 1,
            }
            res = {"warning": {"title": _("Info"), "type": "success", "message": message}}
        self.label_lines._compute_price()
        return res


class ProductProductLabelLine(models.TransientModel):
    _name = "product.product.label.line"
    _description = "product.product.label.line"

    label_id = fields.Many2one(comodel_name="product.product.label", string="Product Label")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    quantity = fields.Integer(string="Label Qty", default=1)

    barcode_image = fields.Binary(string="Barcode Image", compute="_compute_barcode_image")

    lot = fields.Char()
    price = fields.Float(compute="_compute_price")

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

    def _compute_price(self):
        for label_line in self:
            if label_line.label_id.pricelist_id:
                # compute price based on pricelist
                label_line.price = label_line.label_id.pricelist_id._get_product_price(
                    label_line.product_id, quantity=1
                )
            else:
                label_line.price = label_line.product_id.lst_price

    def get_barcode_url(self, code_format="Code128", barcode="", width=200, height=60, humanreadable=1, quiet=0):
        self.ensure_one()
        if self.product_id:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            # url = "{}/report/barcode/{}/{}".format(base_url, format, barcode)
            url = f"{base_url}/report/barcode/?barcode_type={code_format}&value={barcode}&width={width}&height={height}&humanreadable={humanreadable}&quiet={quiet}"

            return url
        else:
            return False
