# ©  2008-2021 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class StockLotTag(models.Model):
    _name = "stock.lot.tag"
    _description = "Stock Lot Tag"

    name = fields.Char(string="Name")


class ProductionLot(models.Model):
    _inherit = "stock.production.lot"

    has_info = fields.Boolean("Has other info")
    inventory_value = fields.Float(store=True)
    categ_id = fields.Many2one("product.category", related="product_id.categ_id", store=True)
    input_price = fields.Float(string="Input Price")
    input_date = fields.Date(string="Input date")
    input_amount = fields.Float(string="Input Amount", compute="_compute_input_amount", store=True)
    tag_ids = fields.Many2many("stock.lot.tag", "stock_lot_tags", "lot_id", "tag_id", string="Tags")
    # RSY fields
    contor_monocrom = fields.Integer(string="Contor monocrom")
    contor_color = fields.Integer(string="Contor color")
    rezervat = fields.Boolean(string="Rezervat")
    rezervat_pentru = fields.Many2one("res.partner", string="Rezervat pentru")
    rezervat_nota = fields.Char("Nota rezervare")
    rezervat_user_id = fields.Many2one("res.users", string="Rezervat de")
    rezervat_date = fields.Date("Data rezervarii")
    equi_categ_id = fields.Many2one("service.equipment.category", string="Categorie echipament")
    pret_final = fields.Float(string="Pret client final", compute="_compute_price")
    pret_final_currency_id = fields.Many2one(
        "res.currency", string="Moneda pret lista", compute="_compute_price", readonly=True
    )
    pret_revanzator = fields.Float(string="Pret revanzator", compute="_compute_price")
    pret_revanzator_currency_id = fields.Many2one(
        "res.currency", string="Moneda pret revanzator", compute="_compute_price", readonly=True
    )
    verificat = fields.Boolean("Echipament Verificat")
    verificat_user_id = fields.Many2one("res.users", string="Verificat de")
    verificat_date = fields.Date("Data verificarii")

    nota_interna = fields.Text()

    @api.depends("input_price", "product_qty")
    def _compute_input_amount(self):
        for lot in self:
            lot.input_amount = lot.input_price * lot.product_qty

    @api.depends("output_price", "product_qty")
    def _compute_output_amount(self):
        for lot in self:
            lot.output_amount = lot.output_price * lot.product_qty

    def _compute_price(self):
        if "pricelist_id" in self.env.context:
            pricelist = self.env["product.pricelist"].browse(self.env.context["pricelist_id"])
            list_currency_id = pricelist.currency_id
        else:
            pricelist = False
            list_currency_id = False

        for serial in self:
            serial.pret_final = serial.product_id.list_price
            serial.pret_final_currency_id = serial.product_id.currency_id
            if pricelist:
                price = pricelist.price_get(serial.product_id.id, serial.product_qty)
                if price:
                    serial.pret_revanzator = price[pricelist.id]
                    serial.pret_revanzator_currency_id = list_currency_id
                else:
                    serial.pret_revanzator = serial.product_id.list_price
                    serial.pret_revanzator_currency_id = serial.product_id.currency_id
            else:
                serial.pret_revanzator = serial.product_id.list_price
                serial.pret_revanzator_currency_id = serial.product_id.currency_id

    def write(self, values):
        if "rezervat" in values:
            if values["rezervat"]:
                values["rezervat_user_id"] = self.env.uid
                values["rezervat_date"] = fields.datetime.now()
            else:
                values["rezervat_user_id"] = False
                values["rezervat_date"] = False
        if "verificat" in values:
            if values["verificat"]:
                values["verificat_user_id"] = self.env.uid
                values["verificat_date"] = fields.datetime.now()
            else:
                values["verificat_user_id"] = False
                values["verificat_date"] = False

        return super(ProductionLot, self).write(values)
