from odoo import models

PRODUCT_IMAGE_FIELDS = [f"image_{size}" for size in [1920, 1024, 512, 256, 128]]


def _get_current_website(env):
    # 20.0: website.get_current_website() was removed; on routes without
    # website=True (e.g. /web/image) the website is in the context as host_id
    return env.website or env["website"].browse(env.context.get("host_id"))


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_placeholder_filename(self, field):
        if field in PRODUCT_IMAGE_FIELDS:
            website = _get_current_website(self.env)
            if website and website.product_placeholder_image:
                return f"website/{website.id}/product_placeholder_image"
            return "deltatech_website_product_placeholder/static/img/placeholder.png"
        return super()._get_placeholder_filename(field)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_placeholder_filename(self, field):
        if field in PRODUCT_IMAGE_FIELDS:
            website = _get_current_website(self.env)
            if website and website.product_placeholder_image:
                return f"website/{website.id}/product_placeholder_image"
            return "deltatech_website_product_placeholder/static/img/placeholder.png"
        return super()._get_placeholder_filename(field)
