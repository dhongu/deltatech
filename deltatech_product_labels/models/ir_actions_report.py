# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import re

from odoo import fields, models

# 40x30, 100 x 50, 58×43 in the name of the layout, in millimeters
SIZE_IN_NAME = re.compile(r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE)
DPI_IN_NAME = re.compile(r"(\d+)\s*dpi", re.IGNORECASE)
DPI_TO_DPMM = {152: "6", 203: "8", 300: "12", 600: "24"}


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    zpl_label_width = fields.Float("Label width (mm)", help="Size of a ZPL label, used by the label preview")
    zpl_label_height = fields.Float("Label height (mm)", help="Size of a ZPL label, used by the label preview")
    zpl_dpmm = fields.Selection(
        [("6", "152 dpi"), ("8", "203 dpi"), ("12", "300 dpi"), ("24", "600 dpi")],
        string="Printer resolution",
        help="Resolution of the ZPL printer, used by the label preview",
    )

    def _get_zpl_label_size(self):
        """Width and height in mm and the resolution in dots/mm of a ZPL label.

        Without explicit values they are read from the name of the layout ("Labels 40x30 ZPL (203 DPI)"),
        then the defaults of a 4x6 inch label at 203 dpi are used.
        """
        self.ensure_one()
        width, height = self.zpl_label_width, self.zpl_label_height
        if not (width and height):
            match = SIZE_IN_NAME.search(self.name or "")
            if match:
                width, height = (float(value.replace(",", ".")) for value in match.groups())
            else:
                width, height = 101.6, 152.4
        dpmm = self.zpl_dpmm
        if not dpmm:
            match = DPI_IN_NAME.search(self.name or "")
            dpmm = DPI_TO_DPMM.get(int(match.group(1)), "8") if match else "8"
        return width, height, dpmm
