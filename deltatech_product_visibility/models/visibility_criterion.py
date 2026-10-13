# ©  2025 Terrabit
#              Voicu Stefan <stefan(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import fields, models

# Codurile sunt fixe (mapate în product.template._get_visibility_checks);
# ponderile și starea activ/inactiv sunt configurabile fără cod.
CRITERION_CODES = [
    ("seo", "SEO complet (titlu + descriere + cuvinte cheie)"),
    ("main_image", "Imagine principală"),
    ("website_description", "Descriere website (amplă)"),
    ("public_category", "Categorie publică"),
    ("gallery", "Galerie de imagini (≥ 2)"),
    ("ecommerce_description", "Descriere eCommerce (scurtă)"),
    ("sale_price", "Preț de vânzare setat"),
    ("default_code", "Cod produs (SKU)"),
]


class ProductVisibilityCriterion(models.Model):
    _name = "deltatech.product.visibility.criterion"
    _description = "Criteriu de vizibilitate a produsului"
    _order = "sequence, weight desc, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Selection(selection=CRITERION_CODES, required=True)
    weight = fields.Integer(default=10, required=True, help="Punctele acordate când criteriul este îndeplinit.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "unique(code)",
        "Există deja un criteriu pentru acest tip de verificare.",
    )

    def action_recompute_scores(self):
        """Reevaluează scorul pentru toate produsele (util după modificarea ponderilor)."""
        products = self.env["product.template"].with_context(active_test=False).search([])
        products._compute_website_visibility()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": "Scorurile de vizibilitate au fost recalculate.",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
