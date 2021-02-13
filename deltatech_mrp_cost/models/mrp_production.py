# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    production_id = fields.Many2one("mrp.production")


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    amount = fields.Float(digits="Account", string="Production Amount", compute="_compute_amount")
    calculate_price = fields.Float(digits="Account", string="Calculate Price", compute="_compute_amount")
    service_amount = fields.Float(
        digits="Account",
        string="Service Amount",
        compute="_compute_service_amount",
        inverse="_inverse_service_amount",
        store=True,
    )
    overhead_amount = fields.Float(string="Overhead", compute="_compute_amount", default="0.0")
    acc_move_line_ids = fields.One2many("account.move.line", "production_id", string="Account move lines")

    @api.depends("move_raw_ids.quantity_done", "move_raw_ids.product_qty")
    def _compute_service_amount(self):
        for production in self:
            service_amount = 0.0
            for move in production.move_raw_ids:
                if move.product_id.type != "product":
                    qty = move.quantity_done or move.product_qty
                    service_amount += move.price_unit * qty
            production.service_amount = service_amount

    def _inverse_service_amount(self):
        service_amount = self.service_amount
        service_product = self.env["product.product"]
        for move in self.move_raw_ids:
            if move.product_id.type != "product":
                service_product |= move.product_id
                qty = move.quantity_done or move.product_qty
        if len(service_product) == 1 and qty:
            price = service_amount / qty
            service_product.write({"standard_price": price})

    def _compute_amount(self):
        for production in self:
            # calculate_price = 0.0
            amount = 0.0
            # service_amount = 0.0
            planned_cost = True
            for move in production.move_raw_ids:
                if move.quantity_done > 0:
                    planned_cost = False  # nu au fost facute miscari de stoc

            if planned_cost:
                for move in production.move_raw_ids:
                    if move.product_id.type == "product":
                        qty = move.product_qty + move.product_qty * move.product_id.scrap
                        amount += move.price_unit * qty
                product_qty = production.product_qty

            else:
                for move in production.move_raw_ids:
                    if move.product_id.type == "product":
                        qty = move.quantity_done
                        amount += abs(move.price_unit) * qty
                product_qty = 0.0
                for move in production.move_finished_ids:
                    product_qty += move.quantity_done
                if product_qty == 0.0:
                    product_qty = production.product_qty

            # adaugare manopera la costul estimat

            if production.routing_id:
                for operation in production.routing_id.operation_ids:
                    time_cycle = operation.get_time_cycle(quantity=product_qty, product=production.product_id)

                    cycle_number = math.ceil(product_qty / operation.workcenter_id.capacity)
                    duration_expected = (
                        operation.workcenter_id.time_start
                        + operation.workcenter_id.time_stop
                        + cycle_number * time_cycle * 100.0 / operation.workcenter_id.time_efficiency
                    )

                    amount += (duration_expected / 60) * operation.workcenter_id.costs_hour

            amount += production.service_amount
            calculate_price = amount / product_qty
            production.calculate_price = calculate_price
            production.amount = amount

    def _cal_price(self, consumed_moves):
        super(MrpProduction, self)._cal_price(consumed_moves)
        self.ensure_one()
        production = self

        self._calculate_amount()  # refac calculul
        price_unit = production.calculate_price
        self.move_finished_ids.write({"price_unit": price_unit})
        # functia standard nu permite si de aceea am facut o modificare in deltatech_purchase_price
        self.move_finished_ids.product_price_update_before_done()

        # if production.product_tmpl_id.cost_method == 'fifo' and
        # production.product_tmpl_id.standard_price != production.calculate_price:
        #
        #     price_unit = production.calculate_price
        #     production.product_tmpl_id.write({'standard_price': price_unit})
        #     production.product_tmpl_id.product_variant_ids.write({'standard_price': price_unit})
        #     production.move_finished_ids.write({'price_unit': price_unit})

        return True

    def check_service_invoiced(self):
        # sunt servicii in bom ?
        for production in self:
            service_amount = 0
            for line in production.bom_id.bom_line_ids:
                if line.product_id.type == "service":
                    # care este comanda de achizitie ?
                    orders = self.env["purchase.order"].search([("group_id", "=", production.procurement_group_id.id)])
                    for order in orders:
                        if order.invoice_status != "invoiced":
                            raise UserError(_("Order %s is not invoiced") % order.name)
                        for invoice in order.invoice_ids:
                            if not invoice.move_id:
                                raise UserError(_("Invoice %s is not validated") % invoice.number)
                            else:
                                for acc_move_line in invoice.move_id.line_ids:
                                    acc_move_line.write({"production_id": production.id})
                                    if acc_move_line.product_id:
                                        service_amount += acc_move_line.debit + acc_move_line.credit
            if service_amount:
                production.write({"service_amount": service_amount})

    def post_inventory(self):
        self.check_service_invoiced()

        self.assign_picking()
        res = super(MrpProduction, self).post_inventory()
        for production in self:
            acc_move_line_ids = self.env["account.move.line"]
            for move in production.move_raw_ids:
                acc_move_line_ids |= move.account_move_ids.line_ids
            for move in production.move_finished_ids:
                acc_move_line_ids |= move.account_move_ids.line_ids
            if acc_move_line_ids:
                acc_move_line_ids.write({"production_id": production.id})
        return res

    def _generate_moves(self):
        res = super(MrpProduction, self)._generate_moves()
        self.assign_picking()
        return res

    def assign_picking(self):
        """
        Toate produsele consumate se vor reuni intr-un picking list (Bon de consum)
        toate produsele receptionate (de regula un singur produs) se vor reuni intr-un picking list (Nota de predare)
        """
        for production in self:
            # bon de consum
            move_list = self.env["stock.move"]
            picking = False
            for move in production.move_raw_ids:
                if not move.picking_id:
                    move_list += move
                else:
                    picking = move.picking_id
            if move_list:

                warehouse_id = production.location_dest_id.get_warehouse() or self.env.user.company_id.warehouse_id
                picking_type = warehouse_id.pick_type_prod_consume_id
                if picking_type:
                    if not picking:
                        picking = self.env["stock.picking"].create(
                            {
                                "picking_type_id": picking_type.id,
                                "date": production.date_planned_start,
                                "location_id": picking_type.default_location_src_id.id,
                                "location_dest_id": picking_type.default_location_dest_id.id,
                                "origin": production.name,
                            }
                        )
                    move_list.write({"picking_id": picking.id})
                    # picking.action_assign()

            # nota de predare
            move_list = self.env["stock.move"]
            picking = False
            for move in production.move_finished_ids:
                if not move.picking_id:
                    move_list += move
                else:
                    picking = move.picking_id
            if move_list:
                warehouse_id = production.location_src_id.get_warehouse() or self.env.user.company_id.warehouse_id

                picking_type = warehouse_id.pick_type_prod_receipt_id
                if picking_type:
                    if not picking:
                        picking = self.env["stock.picking"].create(
                            {
                                "picking_type_id": picking_type.id,
                                "date": production.date_planned_start,
                                "location_id": picking_type.default_location_src_id.id,
                                "location_dest_id": picking_type.default_location_dest_id.id,
                                "origin": production.name,
                            }
                        )
                    move_list.write({"picking_id": picking.id})
                    # picking.action_assign()
        return

    def action_see_picking(self):
        pickings = self.env["stock.picking"]
        for move in self.move_raw_ids:
            pickings |= move.picking_id
        for move in self.move_finished_ids:
            pickings |= move.picking_id

        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        if pickings:
            action["domain"] = "[('id','in'," + str(pickings.ids) + " )]"

        else:
            action = False
        return action

    def _generate_raw_move(self, bom_line, line_data):
        move = super(MrpProduction, self)._generate_raw_move(bom_line, line_data)
        if bom_line.product_id.type == "service":
            self._action_launch_procurement_rule(bom_line, line_data)
        # if bom_line.product_id.type != 'product':
        #     self.service_amount += bom_line.product_id.standard_price * line_data['qty']

        return move

    @api.model
    def _prepare_service_procurement_values(self):
        location = self.location_src_id
        return {
            "company_id": self.company_id,
            "date_planned": self.date_planned_start,
            "warehouse_id": location.get_warehouse(),
            "group_id": self.procurement_group_id,
        }

    @api.model
    def _action_launch_procurement_rule(self, bom_line, line_data):
        values = self._prepare_service_procurement_values()

        name = "{} for {}".format(bom_line.product_id.name, self.name)
        self.env["procurement.group"].sudo().run(
            bom_line.product_id, line_data["qty"], bom_line.product_uom_id, self.location_src_id, name, name, values
        )
        return True
