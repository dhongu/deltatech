# ©  2015-2020 Terrabit
# See README.rst file on addons root folder for license details

import textwrap

from odoo import models
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_open_label_layout(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        override_print_button = safe_eval(get_param("terrabit_labels.override_print_button", "True"))
        action_standard = super().action_open_label_layout()
        if override_print_button:
            xml_id = "deltatech_product_labels.action_action_product_template_label"
            action = self.env["ir.actions.act_window"]._for_xml_id(xml_id)
            return action or action_standard
        else:
            return action_standard


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_wrapped(self, length):
        return textwrap.wrap(self.with_context(display_default_code=False).display_name, length)

    def action_open_label_layout(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        override_print_button = safe_eval(get_param("terrabit_labels.override_print_button", "True"))
        action_standard = super().action_open_label_layout()
        if override_print_button:
            xml_id = "deltatech_product_labels.action_action_product_template_label"
            action = self.env["ir.actions.act_window"]._for_xml_id(xml_id)
            return action or action_standard
        else:
            return action_standard
