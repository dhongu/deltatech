# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def show_order_lines(self):
        """Open enhanced view of order lines with vendor pricelist integration."""
        self.ensure_one()

        action = {
            "type": "ir.actions.act_window",
            "name": f"Purchase Order Lines - {self.name}",
            "res_model": "purchase.order.line",
            "view_mode": "tree,form",
            "views": [(self.env.ref("deltatech_purchase_xls.purchase_order_line_tree_enhanced").id, "tree")],
            "domain": [("order_id", "=", self.id)],
            "context": {
                "default_order_id": self.id,
                "create": True,
                "edit": True,
                "search_default_order_id": self.id,
            },
        }
        return action


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    partner_ref = fields.Char(
        string="Vendor Product Code",
        help="Vendor's product code/reference for this product",
        compute="_compute_partner_ref",
        store=True,
        readonly=False
    )

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_partner_ref(self):
        """Automatically populate vendor code from vendor pricelist."""
        for line in self:
            if line.product_id and line.order_id.partner_id:
                # Search for vendor pricelist entry
                supplier_info = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                    ('partner_id', '=', line.order_id.partner_id.id),
                ], limit=1, order='min_qty ASC')
                
                if supplier_info:
                    line.partner_ref = supplier_info.product_code or supplier_info.product_name
                else:
                    # Fallback to product default code
                    line.partner_ref = line.product_id.default_code or ''
            else:
                line.partner_ref = ''

    @api.onchange('product_id')
    def _onchange_product_id_vendor_info(self):
        """Update price and vendor code when product changes."""
        if self.product_id and self.order_id.partner_id:
            # Get vendor pricelist info
            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('partner_id', '=', self.order_id.partner_id.id),
                ('min_qty', '<=', self.product_qty or 1),
            ], limit=1, order='min_qty DESC')
            
            if supplier_info:
                self.partner_ref = supplier_info.product_code or supplier_info.product_name
                # Update price if found in vendor pricelist
                if supplier_info.price > 0:
                    self.price_unit = supplier_info.price

    def get_vendor_pricelist_info(self):
        """Get vendor pricelist information for this line."""
        self.ensure_one()
        if not self.product_id or not self.order_id.partner_id:
            return {}
            
        supplier_info = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('partner_id', '=', self.order_id.partner_id.id),
        ], order='min_qty ASC')
        
        return {
            'supplier_infos': supplier_info,
            'vendor_codes': supplier_info.mapped('product_code'),
            'vendor_names': supplier_info.mapped('product_name'),
        }
