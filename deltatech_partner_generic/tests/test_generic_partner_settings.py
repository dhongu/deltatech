from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGenericPartnerSettings(TransactionCase):
    def test_setting_is_in_invoicing_settings(self):
        arch = self.env["res.config.settings"].get_view(view_type="form")["arch"]
        doc = etree.fromstring(arch)

        self.assertTrue(doc.xpath("//app[@name='account']//field[@name='generic_partner_id']"))
        self.assertTrue(doc.xpath("//app[@name='account']//field[@name='lock_generic_partner']"))
