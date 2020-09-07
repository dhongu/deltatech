# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models, fields, _
import odoo.addons.decimal_precision as dp


def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r


class mrp_product_produce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def do_produce(self, cr, uid, ids, context=None):
        production_id = context.get('active_id', False)
        assert production_id, "Production Id should be specified in context as a Active ID."
        data = self

        # daca se modifica lista de materiale trebuie sa indentific care meteriale au fost adaugate noi
        production_obj = self.pool.get('mrp.production')
        production = production_obj.browse(cr, uid, production_id, context=context)
        for consume in data.consume_lines:
            raw_mat_add = True
            for raw_material_line in production.move_lines:
                if consume.product_id.id == raw_material_line.product_id.id:
                    raw_mat_add = False

            if raw_mat_add:
                production_obj._make_consume_line_from_data(cr, uid, production, consume.product_id,
                                                            consume.product_id.uom_id.id, consume.product_qty, False, 0,
                                                            context=context)

        for raw_material_line in production.move_lines:
            raw_mat_del = True
            for consume in data.consume_lines:
                if consume.product_id.id == raw_material_line.product_id.id:
                    raw_mat_del = False
            if raw_mat_del:
                self.pool.get('stock.move').action_cancel(cr, uid, raw_material_line.id)

        production_obj.action_produce(cr, uid, production_id, data.product_qty, data.mode, data, context=context)
        return {}


class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    def calc_price(self, cr, uid, bom_id, context=None):
        bom = self.browse(cr, uid, bom_id, context=context)
        amount = 0
        for line in bom.bom_line_ids:
            amount += line.calculate_price * line.product_qty

        price = amount / bom.product_qty + amount / bom.product_qty * bom.value_overhead
        return price

    def _calculate_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for bom in self.browse(cr, uid, ids, context=context):
            res[bom.id] = self.calc_price(cr, uid, bom.id, context)
        return res

    def _calculate_standard_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for bom in self.browse(cr, uid, ids, context=context):
            if bom.product_id:
                res[bom.id] = bom.product_id.standard_price
            else:
                res[bom.id] = bom.product_tmpl_id.standard_price
        return res

    value_overhead = fields.Float('Value Overhead', help="For Value Overhead percent enter % ratio between 0-1."),
    calculate_price = fields.Float(_calculate_price, digits_compute=dp.get_precision('Product Price'), store=True,
                                   string='Calculate Price'),
    standard_price = fields.Float(_calculate_standard_price, digits_compute=dp.get_precision('Product Price'),
                                  store=False,
                                  string="Standard Price"),

    def _check_percent(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if (obj.value_overhead < 0.0 or obj.value_overhead > 1.0):
            return False
        return True

    _constraints = [
        (_check_percent, 'Percentages for Value Overhead must be between 0 and 1, Example: 0.02 for 2% ',
         ['value_overhead']),
    ]

    _default = {
        'value_overhead': 0.2,
    }

    def _bom_explode(self, cr, uid, bom, product, factor, properties=None, level=0, routing_id=False,
                     previous_products=None, master_bom=None, context=None):
        result, result2 = super(mrp_bom, self)._bom_explode(cr, uid, bom, product, factor, properties, level,
                                                            routing_id, previous_products, master_bom, context)
        uom_obj = self.pool.get("product.uom")
        for res in result:
            res['product_qty'] = uom_obj._compute_qty(cr, uid, res['product_uom'], res['product_qty'],
                                                      res['product_uom'])
        return result, result2


class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'

    def _calculate_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        bom_obj = self.pool['mrp.bom']
        for bom_line in self.browse(cr, uid, ids, context=context):
            bom_id = bom_obj._bom_find(cr, uid, product_tmpl_id=bom_line.product_id.product_tmpl_id.id,
                                       product_id=bom_line.product_id.id, context=context)
            if bom_id:
                child_bom = bom_obj.browse(cr, uid, bom_id, context=context)
                price = child_bom.calculate_price
            else:
                price = bom_line.product_id.standard_price
            res[bom_line.id] = price
        return res

    _columns = {
        'calculate_price': fields.function(_calculate_price, type='float',
                                           digits_compute=dp.get_precision('Product Price'), store=False,
                                           string='Calculate Price'),
        'standard_price': fields.related('product_id', 'standard_price', type="float", relation="product.product",
                                         string="Standard Price", store=False)
    }


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    def _calculate_amount(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for production in self.browse(cr, uid, ids, context=context):
            res[production.id] = {'amount': 0.0, 'calculate_price': 0.0}
            amount = 0.0
            for move in production.move_lines2:
                for quant in move.quant_ids:
                    if quant.qty > 0:
                        amount += quant.cost * quant.qty
            res[production.id]['calculate_price'] = amount / production.product_qty
            res[production.id]['amount'] = amount
        return res

    _columns = {
        'amount': fields.function(_calculate_amount, multi='amount', type='float',
                                  digits_compute=dp.get_precision('Account'), store=False, string='Production Amount'),
        'calculate_price': fields.function(_calculate_amount, multi='amount', type='float',
                                           digits_compute=dp.get_precision('Product Price'), store=False,
                                           string='Calculate Price'),
    }

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms production order.
        @return: Newly generated Shipment Id.
        """

        picking_id = super(mrp_production, self).action_confirm(cr, uid, ids, context)

        lot_obj = self.pool.get('stock.production.lot')
        move_obj = self.pool.get('stock.move')

        prodlot_name = None

        for production in self.browse(cr, uid, ids, context=context):

            for move in production.move_lines:
                # daca produseul este gestionat in loturi se incearca determinarea autmat a lotului disponibil
                """
                if move.product_id.track_production :
                    lot_ids = lot_obj.search(cr, uid,[('product_id','=', move.product_id.id),
                                                      ('stock_available', '>', 0)], order = 'date')
                    if lot_ids:
                        required = move.product_qty
                        for lot in lot_obj.browse(cr,uid,lot_ids):
                            if lot.stock_available > required:
                                move_obj.write(cr, uid, [move.id], {'prodlot_id': lot.id, 'product_qty':required},context=context )
                                break
                            else:
                                new_id = move_obj.copy(cr,uid,move.id,{'prodlot_id': lot.id,'product_qty':lot.stock_available},context=context )
                                self.write(cr,uid,production.id,{'move_lines':[(4,new_id)]})
                                required = required - lot.stock_available
                                move_obj.write(cr, uid, [move.id], {'product_qty':required},context=context )

                    if len(lot_ids) == 1:
                        prodlot_name = lot_obj.browse(cr,uid,lot_ids[0]).name
                  """

                if move.date_expected != production.date_planned:
                    move_obj.write(cr, uid, [move.id], {'date_expected': production.date_planned}, context=context)

            for move in production.move_created_ids:
                if move.date_expected != production.date_planned:
                    move_obj.write(cr, uid, [move.id], {'date_expected': production.date_planned}, context=context)

                # daca produsul este gestionat in loturi atunci se va genera un lot nou la confirmarea comenzii de productie
                """
                if production.product_id.track_production:
                    if not move.prodlot_id:
                        if prodlot_name == None:
                            prodlot_id = lot_obj.create(cr, uid, {'product_id': production.product_id.id,'date': production.date_planned}, context=context )
                        else:
                            prodlot_id = lot_obj.search(cr, uid, [('name', '=', prodlot_name),('product_id','=',production.product_id.id )], context=context)
                            if len(prodlot_id)==0:
                                prodlot_id = lot_obj.create(cr, uid, {'product_id': production.product_id.id , 'name':prodlot_name, 'date': production.date_planned}, context=context )
                            else:
                                prodlot_id = prodlot_id[0]
                        move_obj.write(cr, uid, [move.id], {'prodlot_id': prodlot_id, 'date': production.date_planned }, context=context )
                """
            self.pool.get('stock.picking').write(cr, uid, [picking_id], {'date': production.date_planned},
                                                 context=context)

        #            for move in production.picking_id.move_lines:
        #                self.pool.get('stock.move').write(cr, uid, [move.id], {'date_expected': production.date_planned }, context=context )

        return picking_id


class mrp_production_product_line(models.Model):
    _inherit = 'mrp.production.product.line'

    def onchange_product_id(self, cr, uid, ids, product_id, name, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            v = {'product_uom': prod.uom_id.id,
                 'name': prod.name}
            return {'value': v}
        return {}

    qty_available = fields.Float(related='product_id.qty_available', string="Real Stock", store=False, readonly=True)
