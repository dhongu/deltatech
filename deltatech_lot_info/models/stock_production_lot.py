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
    # categ_id = fields.Many2one(
    #     "product.category", string="Internal Category", related="product_id.categ_id", store=True, readonly=True
    # )
    categ_id = fields.Many2one("product.category", related="product_id.categ_id", store=True)
    input_price = fields.Float(string="Input Price")
    output_price = fields.Float(string="Output Price")
    input_date = fields.Date(string="Input date")
    output_date = fields.Date(string="Output date")
    input_amount = fields.Float(string="Input Amount", compute="_compute_input_amount", store=True)
    output_amount = fields.Float(string="Output Amount", compute="_compute_output_amount", store=True)

    customer_id = fields.Many2one("res.partner", string="Customer")
    supplier_id = fields.Many2one("res.partner", string="Supplier")
    origin = fields.Char(string="Source Document")
    sale_invoice_id = fields.Many2one("account.move", string="Invoice")
    tag_ids = fields.Many2many("stock.lot.tag", string="Tags")

    # RSY fields
    contor_monocrom = fields.Integer(string="Contor monocrom")
    contor_color = fields.Integer(string="Contor color")
    rezervat = fields.Boolean(string='Rezervat')
    rezervat_pentru = fields.Many2one('res.partner', string='Rezervat pentru')
    rezervat_nota = fields.Char('Nota rezervare')
    rezervat_user_id = fields.Many2one('res.users', string="Rezervat de")
    rezervat_date = fields.Date('Data rezervarii')
    equi_categ_id = fields.Many2one('service.equipment.category', string="Categorie echipament")

    # pret_final = fields.Float(string="Pret client final", compute='_compute_price')
    # pret_final_currency_id = fields.Many2one('res.currency', string='Moneda pret lista', compute='_compute_price',
    #                                          readonly=True)
    # pret_revanzator = fields.Float(string="Pret revanzator", compute='_compute_price')
    # pret_revanzator_currency_id = fields.Many2one('res.currency', string='Moneda pret revanzator',
    #                                               compute='_compute_price', readonly=True)

    pret_final = fields.Float(string="Pret client final")
    pret_final_currency_id = fields.Many2one('res.currency', string='Moneda pret lista')
    pret_revanzator = fields.Float(string="Pret revanzator")
    pret_revanzator_currency_id = fields.Many2one('res.currency', string='Moneda pret revanzator')

    verificat = fields.Boolean('Echipament Verificat')
    verificat_user_id = fields.Many2one('res.users', string="Verificat de")
    verificat_date = fields.Date('Data verificarii')

    nota_interna = fields.Text()

    @api.depends("input_price", "product_qty")
    def _compute_input_amount(self):
        for lot in self:
            lot.input_amount = lot.input_price * lot.product_qty

    @api.depends("output_price", "product_qty")
    def _compute_output_amount(self):
        for lot in self:
            lot.output_amount = lot.output_price * lot.product_qty


