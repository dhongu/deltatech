# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import hashlib

from odoo import api, fields, models
from odoo.tools import SQL

# câmpul original al lui image.mixin; variantele redimensionate sunt derivate din el
IMAGE_FIELD = "image_1920"


class ProductImage(models.Model):
    _inherit = "product.image"

    image_checksum = fields.Char(
        string="Image Checksum",
        compute="_compute_image_checksum",
        store=True,
        index=True,
        readonly=True,
        help="SHA1 of the original image. Two images with the same checksum have byte-identical content.",
    )
    duplicate_count = fields.Integer(
        string="Copies",
        compute="_compute_duplicate_count",
        help="How many product images in the database share this exact content, including this one.",
    )

    # === COMPUTE METHODS ===#

    @api.depends(IMAGE_FIELD)
    def _compute_image_checksum(self):
        checksums = self._dedup_attachment_checksums()
        for image in self:
            checksum = checksums.get(image.id)
            if not checksum and image[IMAGE_FIELD]:
                # atașamentul nu e (încă) scris — calculăm noi, cu același algoritm
                # ca ir.attachment._compute_checksum, ca valorile să fie comparabile
                checksum = hashlib.sha1(base64.b64decode(image[IMAGE_FIELD])).hexdigest()
            image.image_checksum = checksum or False

    def _compute_duplicate_count(self):
        checksums = [checksum for checksum in set(self.mapped("image_checksum")) if checksum]
        counts = {}
        if checksums:
            groups = self.env["product.image"]._read_group(
                [("image_checksum", "in", checksums)], ["image_checksum"], ["__count"]
            )
            counts = dict(groups)
        for image in self:
            image.duplicate_count = counts.get(image.image_checksum, 0)

    # === HELPERS ===#

    def _dedup_attachment_checksums(self):
        """Checksum-ul fiecărei imagini, citit din ir.attachment.

        Odoo calculează deja SHA1 la scrierea atașamentului, deci nu decodăm
        nicio imagine. ``res_field`` e dat explicit fiindcă ``ir.attachment._search``
        exclude implicit atașamentele-câmp, chiar pentru admin.
        """
        real_ids = [image_id for image_id in self.ids if isinstance(image_id, int)]
        if not real_ids:
            return {}
        attachments = (
            self.env["ir.attachment"]
            .sudo()
            .search_read(
                [
                    ("res_model", "=", self._name),
                    ("res_field", "=", IMAGE_FIELD),
                    ("res_id", "in", real_ids),
                ],
                ["res_id", "checksum"],
            )
        )
        return {att["res_id"]: att["checksum"] for att in attachments if att["checksum"]}

    @api.model
    def _dedup_backfill_checksums(self):
        """Populează ``image_checksum`` pentru tot catalogul, dintr-un singur UPDATE.

        Computarea prin ORM ar citi fiecare imagine din filestore; pe un catalog
        de sute de mii de imagini asta durează ore. Checksum-ul e deja în
        ir_attachment, așa că îl copiem direct.
        """
        # fără flush, un write pending pe image_checksum s-ar scrie DUPĂ UPDATE-ul
        # nostru și l-ar anula
        self.env.flush_all()
        self.env.cr.execute(
            SQL(
                """
                UPDATE product_image pi
                   SET image_checksum = att.checksum
                  FROM ir_attachment att
                 WHERE att.res_model = %s
                   AND att.res_field = %s
                   AND att.res_id = pi.id
                   AND att.checksum IS NOT NULL
                   AND pi.image_checksum IS DISTINCT FROM att.checksum
                """,
                self._name,
                IMAGE_FIELD,
            )
        )
        updated = self.env.cr.rowcount
        self.env.invalidate_all(flush=False)
        return updated

    # === ACTIONS ===#

    def action_view_duplicates(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Copies of this image"),
            "res_model": "product.image",
            "views": [
                (self.env.ref("deltatech_image_optimize.view_product_image_dedup_list").id, "list"),
                (False, "form"),
            ],
            "domain": [("image_checksum", "=", self.image_checksum)],
        }
