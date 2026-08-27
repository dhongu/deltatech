# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools
from odoo.tools import SQL


class ProductImageDuplicate(models.Model):
    """Grupurile de imagini identice, o linie per conținut distinct.

    Vederea nu ține date proprii: se recalculează la fiecare interogare din
    ``product_image.image_checksum``, care e indexat.
    """

    _name = "deltatech.product.image.duplicate"
    _description = "Duplicated Product Image"
    _auto = False
    _order = "image_count desc"

    image_checksum = fields.Char(string="Image Checksum", readonly=True)
    image_count = fields.Integer(string="Copies", readonly=True, aggregator="sum")
    product_count = fields.Integer(
        string="Products",
        readonly=True,
        aggregator="sum",
        help="How many distinct products (or variants) use this image.",
    )
    removable_count = fields.Integer(
        string="Removable",
        readonly=True,
        aggregator="sum",
        help="Copies that repeat inside the same product. Removing them loses nothing — "
        "every product keeps one copy of the image.",
    )
    sample_image = fields.Binary(string="Image", compute="_compute_sample", compute_sudo=True)
    product_names = fields.Char(string="Used On", compute="_compute_sample", compute_sudo=True)

    # === COMPUTE METHODS ===#

    def _compute_sample(self):
        for group in self:
            images = self.env["product.image"].search([("image_checksum", "=", group.image_checksum)], limit=10)
            group.sample_image = images[:1].image_256 or False
            names = images.mapped(lambda image: image.product_tmpl_id.display_name or image.display_name)
            group.product_names = ", ".join(dict.fromkeys(name for name in names if name))

    # === SETUP ===#

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            SQL(
                """
                CREATE VIEW %s AS (
                    SELECT min(pi.id)                       AS id,
                           pi.image_checksum                AS image_checksum,
                           count(*)                         AS image_count,
                           count(DISTINCT (
                               COALESCE(pi.product_tmpl_id, 0),
                               COALESCE(pi.product_variant_id, 0)
                           ))                               AS product_count,
                           count(*) - count(DISTINCT (
                               COALESCE(pi.product_tmpl_id, 0),
                               COALESCE(pi.product_variant_id, 0)
                           ))                               AS removable_count
                      FROM product_image pi
                     WHERE pi.image_checksum IS NOT NULL
                     GROUP BY pi.image_checksum
                    HAVING count(*) > 1
                )
                """,
                SQL.identifier(self._table),
            )
        )

    # === ACTIONS ===#

    def action_view_images(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Duplicated Images"),
            "res_model": "product.image",
            "views": [
                (self.env.ref("deltatech_image_optimize.view_product_image_dedup_list").id, "list"),
                (False, "form"),
            ],
            "domain": [("image_checksum", "in", self.mapped("image_checksum"))],
        }

    def action_clean(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Remove Duplicated Images"),
            "res_model": "deltatech.product.image.dedup",
            "view_mode": "form",
            "target": "new",
            "context": {"active_model": self._name, "active_ids": self.ids},
        }
