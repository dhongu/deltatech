# © 2024 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestWebsiteFloatingWidget(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Widget = cls.env["website.floating.widget"]

    def test_01_widget_defaults(self):
        """Test default values of a new widget"""
        widget = self.Widget.create(
            {
                "name": "Test Widget",
                "link": "https://example.com",
            }
        )
        self.assertEqual(widget.icon, "fa-info")
        self.assertEqual(widget.type, "url")
        self.assertEqual(widget.button_shape, "circle")
        self.assertTrue(widget.active)
        self.assertTrue(widget.display_on_desktop)
        self.assertTrue(widget.display_on_mobile)
        self.assertEqual(widget.background_color, "#875A7B")
        self.assertEqual(widget.text_color, "#FFFFFF")

    def test_02_get_link(self):
        """Test the get_link method for different types"""
        # URL type
        widget_url = self.Widget.create({"name": "URL Widget", "link": "https://example.com", "type": "url"})
        self.assertEqual(widget_url.get_link(), "https://example.com")

        # Phone type
        widget_phone = self.Widget.create({"name": "Phone Widget", "link": "123456789", "type": "phone"})
        self.assertEqual(widget_phone.get_link(), "tel:123456789")

        # Email type
        widget_email = self.Widget.create({"name": "Email Widget", "link": "test@example.com", "type": "email"})
        self.assertEqual(widget_email.get_link(), "mailto:test@example.com")

    def test_03_icon_preview(self):
        """Test the computed icon_preview field"""
        widget = self.Widget.create(
            {
                "name": "Preview Widget",
                "icon": "fa-phone",
                "link": "123456789",
            }
        )
        self.assertIn("fa-phone", widget.icon_preview)
        self.assertIn('style="font-size: 24px;"', widget.icon_preview)

        widget.icon = "fa-envelope"
        self.assertIn("fa-envelope", widget.icon_preview)
