from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_website_sale_attribute_filter.controllers.main import WebsiteSaleAttributeFilter
from odoo.addons.website_sale.controllers.main import WebsiteSale


class TestAttributeFilter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = WebsiteSaleAttributeFilter()

        # Create Attributes
        self.attr_color = self.env["product.attribute"].create(
            {
                "name": "Color",
                "display_type": "color",
            }
        )
        self.val_red = self.env["product.attribute.value"].create(
            {
                "name": "Red",
                "attribute_id": self.attr_color.id,
            }
        )
        self.val_blue = self.env["product.attribute.value"].create(
            {
                "name": "Blue",
                "attribute_id": self.attr_color.id,
            }
        )

        self.attr_size = self.env["product.attribute"].create(
            {
                "name": "Size",
                "display_type": "radio",
            }
        )
        self.val_small = self.env["product.attribute.value"].create(
            {
                "name": "Small",
                "attribute_id": self.attr_size.id,
            }
        )
        self.val_large = self.env["product.attribute.value"].create(
            {
                "name": "Large",
                "attribute_id": self.attr_size.id,
            }
        )

        # Create Products
        self.product_red_small = self.env["product.template"].create(
            {
                "name": "Red Small Product",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_color.id,
                            "value_ids": [(6, 0, [self.val_red.id])],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_size.id,
                            "value_ids": [(6, 0, [self.val_small.id])],
                        },
                    ),
                ],
            }
        )

    def test_attribute_filter_logic(self):
        # We need to mock 'request' because the controller uses it
        mock_request = MagicMock()
        mock_request.env = self.env

        with MagicMock() as mock_response:
            mock_response.qcontext = {"search_product": self.product_red_small}

            with (
                patch("odoo.addons.deltatech_website_sale_attribute_filter.controllers.main.request", mock_request),
                patch.object(WebsiteSale, "shop", return_value=mock_response),
            ):
                res = self.controller.shop()

                active_ids = res.qcontext.get("active_attribute_value_ids")

                self.assertIn(self.val_red.id, active_ids)
                self.assertIn(self.val_small.id, active_ids)
                self.assertNotIn(self.val_blue.id, active_ids)
                self.assertNotIn(self.val_large.id, active_ids)

    def test_attribute_filter_empty(self):
        mock_request = MagicMock()
        mock_request.env = self.env

        with MagicMock() as mock_response:
            mock_response.qcontext = {"search_product": self.env["product.template"]}

            with (
                patch("odoo.addons.deltatech_website_sale_attribute_filter.controllers.main.request", mock_request),
                patch.object(WebsiteSale, "shop", return_value=mock_response),
            ):
                res = self.controller.shop()
                active_ids = res.qcontext.get("active_attribute_value_ids")
                self.assertEqual(len(active_ids), 0)
