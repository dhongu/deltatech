from odoo import models

from .product import PRODUCT_IMAGE_FIELDS


class Image(models.AbstractModel):
    _inherit = "ir.qweb.field.image"

    def _get_src_urls(self, record, field_name, options):
        if record._name in ("product.template", "product.product") and field_name in PRODUCT_IMAGE_FIELDS:
            if not record.sudo()[field_name]:
                placeholder = record._get_placeholder_filename(field_name)
                if placeholder:
                    if placeholder.startswith("website/"):
                        return f"/web/image/{placeholder}", None
                    return "/" + placeholder, None

        return super()._get_src_urls(record, field_name, options)
