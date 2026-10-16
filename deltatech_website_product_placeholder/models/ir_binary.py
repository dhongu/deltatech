from odoo import models


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _get_placeholder_stream(self, path=""):
        if path and path.startswith("website/") and path.endswith("/product_placeholder_image"):
            # Format: website/<id>/product_placeholder_image
            parts = path.split("/")
            if len(parts) == 3 and parts[1].isdigit():
                website = self.env["website"].sudo().browse(int(parts[1])).exists()
                if website and website.product_placeholder_image:
                    # 20.0: Stream.from_binary_field was removed, the stream of a
                    # binary field is built by ir.binary._record_to_stream
                    stream = self._record_to_stream(website, "product_placeholder_image")
                    if not stream.mimetype:
                        stream.mimetype = website.product_placeholder_image.mimetype
                    return stream
        return super()._get_placeholder_stream(path)
