from odoo import models
from odoo.http import Stream


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _get_placeholder_stream(self, path=None):
        if path and path.startswith("website/") and path.endswith("/product_placeholder_image"):
            # Format: website/<id>/product_placeholder_image
            parts = path.split("/")
            if len(parts) == 3:
                website_id = int(parts[1])
                website = self.env["website"].browse(website_id)
                if website.exists() and website.product_placeholder_image:
                    return Stream.from_binary_field(website, "product_placeholder_image")
        return super()._get_placeholder_stream(path)
