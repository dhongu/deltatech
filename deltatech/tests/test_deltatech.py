# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDeltatech(TransactionCase):
    def test_access_model_name(self):
        """model_name on ir.access follows the technical name of the model"""
        access = self.env["ir.access"].create(
            {
                "name": "Test partner access",
                "model_id": self.env.ref("base.model_res_partner").id,
                "group_id": self.env.ref("base.group_user").id,
                "operation": "r",
                "domain": "[('active', '=', True)]",
            }
        )
        self.assertEqual(access.model_name, "res.partner")

    def test_access_form_domain_widget(self):
        """The access form shows model_name and edits the domain with the domain widget"""
        arch = etree.fromstring(self.env["ir.access"].get_view(view_type="form")["arch"])
        self.assertTrue(arch.xpath("//field[@name='model_name']"))
        domain = arch.xpath("//field[@name='domain']")
        self.assertEqual(domain[0].get("widget"), "domain")

    def test_module_form_without_external_link(self):
        """The external pricing link is removed from the module form"""
        arch = etree.fromstring(
            self.env["ir.module.module"].get_view(self.env.ref("base.module_form").id, "form")["arch"]
        )
        self.assertFalse(arch.xpath("//a[contains(@href, 'odoo.com/pricing')]"))
