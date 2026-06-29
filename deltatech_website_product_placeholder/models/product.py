from odoo import models

PRODUCT_IMAGE_FIELDS = [f"image_{size}" for size in [1920, 1024, 512, 256, 128]]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_placeholder_filename(self, field):
        if field in PRODUCT_IMAGE_FIELDS:
            website = self.env["website"].get_current_website()
            if website and website.product_placeholder_image:
                return f"website/{website.id}/product_placeholder_image"
            return "deltatech_website_product_placeholder/static/img/placeholder.png"
        return super()._get_placeholder_filename(field)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_placeholder_filename(self, field):
        if field in PRODUCT_IMAGE_FIELDS:
            website = self.env["website"].get_current_website()
            if website and website.product_placeholder_image:
                return f"website/{website.id}/product_placeholder_image"
            return "deltatech_website_product_placeholder/static/img/placeholder.png"
        return super()._get_placeholder_filename(field)
