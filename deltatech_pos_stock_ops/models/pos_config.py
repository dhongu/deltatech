from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    stock_ops_receipt = fields.Boolean(string="Receipts from the POS")
    stock_ops_delivery = fields.Boolean(string="Deliveries from the POS")
    stock_ops_receipt_type_id = fields.Many2one(
        "stock.picking.type",
        string="Receipt Operation Type",
        compute="_compute_stock_ops_types",
        store=True,
        readonly=False,
        domain="[('code', '=', 'incoming'), ('company_id', '=', company_id)]",
        check_company=True,
    )
    stock_ops_delivery_type_id = fields.Many2one(
        "stock.picking.type",
        string="Delivery Operation Type",
        compute="_compute_stock_ops_types",
        store=True,
        readonly=False,
        domain="[('code', '=', 'outgoing'), ('company_id', '=', company_id)]",
        check_company=True,
    )

    @api.depends("picking_type_id.warehouse_id")
    def _compute_stock_ops_types(self):
        for config in self:
            warehouse = config.picking_type_id.warehouse_id
            if not config.stock_ops_receipt_type_id or config.stock_ops_receipt_type_id.warehouse_id != warehouse:
                config.stock_ops_receipt_type_id = warehouse.in_type_id
            if not config.stock_ops_delivery_type_id or config.stock_ops_delivery_type_id.warehouse_id != warehouse:
                config.stock_ops_delivery_type_id = warehouse.out_type_id
