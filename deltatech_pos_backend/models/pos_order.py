# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def default_get(self, fields_list):
        defaults = super(PosOrder, self).default_get(fields_list)
        active_model = self.env.context.get("active_model", False)
        active_id = self.env.context.get("active_id", False)
        if active_model == "pos.config":
            pos_config = self.env[active_model].browse(active_id)
            session_id = pos_config.current_session_id
            defaults["session_id"] = session_id.id
            defaults["pricelist_id"] = pos_config.pricelist_id.id
            defaults["fiscal_position_id"] = pos_config.default_fiscal_position_id.id
            defaults["company_id"] = pos_config.company_id.id

            defaults["pos_reference"] = "{}-{}-{}".format(
                str(session_id.id).zfill(5),
                str(session_id.login()).zfill(3),
                str(session_id.sequence_number).zfill(4),
            )

        return defaults

    def action_confirm(self):
        for order in self:
            if not order.picking_ids:
                # todo: de pus in configurare daca se confirma automat miscarile de stoc
                order.with_context(from_pos_order_confirm=True)._create_order_picking()

    def unlink(self):
        for order in self:
            order.picking_ids.unlink()
        super(PosOrder, self).unlink()


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    @api.onchange("product_id")
    def _onchange_product_id(self):
        super(PosOrderLine, self)._onchange_product_id()
        if self.product_id:
            self.full_product_name = self.product_id.display_name
