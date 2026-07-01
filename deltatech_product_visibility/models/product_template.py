# ©  2025 Terrabit
#              Voicu Stefan <stefan(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.tools.mail import is_html_empty

# nivel -> (label, culoare semafor)
LEVEL_INFO = {
    "hidden": ("Invizibil", "#E24B4A"),
    "weak": ("Slab", "#EF9F27"),
    "good": ("Bun", "#639922"),
    "optimal": ("Optim", "#0F6E56"),
}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_visibility_score = fields.Integer(
        string="Scor vizibilitate",
        compute="_compute_website_visibility",
        store=True,
        help="Scor 0-100: cât de complet/optimizat este produsul pentru catalogul de pe website.",
    )
    website_visibility_level = fields.Selection(
        selection=[
            ("hidden", "Invizibil"),
            ("weak", "Slab"),
            ("good", "Bun"),
            ("optimal", "Optim"),
        ],
        string="Nivel vizibilitate",
        compute="_compute_website_visibility",
        store=True,
    )
    website_visibility_badge = fields.Html(
        string="Vizibilitate",
        compute="_compute_website_visibility_html",
        sanitize=False,
    )
    website_visibility_detail = fields.Html(
        string="Defalcare vizibilitate",
        compute="_compute_website_visibility_html",
        sanitize=False,
    )

    # -- criterii ------------------------------------------------------------

    def _get_visibility_checks(self):
        """Întoarce {cod_criteriu: bool} - dacă produsul îndeplinește criteriul."""
        self.ensure_one()
        return {
            "seo": bool(self.is_seo_optimized),
            "main_image": bool(self.image_1920),
            "website_description": not is_html_empty(self.website_description),
            "public_category": bool(self.public_categ_ids),
            "gallery": len(self.product_template_image_ids) >= 2,
            "ecommerce_description": not is_html_empty(self.description_ecommerce),
            "sale_price": self.list_price > 0,
            "default_code": bool(self.default_code),
        }

    @staticmethod
    def _visibility_level_for_score(score):
        if score >= 90:
            return "optimal"
        if score >= 70:
            return "good"
        if score >= 40:
            return "weak"
        return "hidden"

    # -- scor ----------------------------------------------------------------

    @api.depends(
        "is_seo_optimized",
        "image_1920",
        "website_description",
        "public_categ_ids",
        "product_template_image_ids",
        "description_ecommerce",
        "list_price",
        "default_code",
    )
    def _compute_website_visibility(self):
        criteria = self.env["deltatech.product.visibility.criterion"].search([])
        weights = {c.code: c.weight for c in criteria}
        total_weight = sum(weights.values())
        for product in self:
            checks = product._get_visibility_checks()
            earned = sum(weights.get(code, 0) for code, met in checks.items() if met)
            # normalizat la 0-100 (robust dacă ponderile nu însumează exact 100)
            score = round(earned * 100 / total_weight) if total_weight else 0
            product.website_visibility_score = score
            product.website_visibility_level = self._visibility_level_for_score(score)

    # -- reprezentare vizuală (semafor + defalcare) --------------------------

    @api.depends(
        "website_visibility_score",
        "website_visibility_level",
        "is_published",
        "is_seo_optimized",
        "image_1920",
        "website_description",
        "public_categ_ids",
        "product_template_image_ids",
        "description_ecommerce",
        "list_price",
        "default_code",
    )
    def _compute_website_visibility_html(self):
        criteria = self.env["deltatech.product.visibility.criterion"].search([])
        for product in self:
            product.website_visibility_badge = product._render_visibility_badge()
            product.website_visibility_detail = product._render_visibility_detail(criteria)

    def _render_visibility_badge(self):
        self.ensure_one()
        level = self.website_visibility_level or "hidden"
        label, color = LEVEL_INFO[level]
        score = self.website_visibility_score
        pub_color, pub_text = ("#0F6E56", "Publicat") if self.is_published else ("#888780", "Nepublicat")
        return Markup(
            '<div style="display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap;">'
            '<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;'
            'border-radius:999px;border:1px solid {color};">'
            '<span style="width:11px;height:11px;border-radius:50%;background:{color};"></span>'
            '<span style="font-weight:500;color:{color};">{score}% · {label}</span>'
            "</span>"
            '<span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;'
            'border-radius:999px;border:1px solid {pub_color};color:{pub_color};font-size:12px;">'
            "{pub_text}</span>"
            "</div>"
        ).format(color=color, score=score, label=label, pub_color=pub_color, pub_text=pub_text)

    def _render_visibility_detail(self, criteria):
        self.ensure_one()
        checks = self._get_visibility_checks()
        missing = Markup("")
        met = Markup("")
        for crit in criteria:
            is_met = checks.get(crit.code, False)
            name = escape(crit.name)
            if is_met:
                met += Markup(
                    '<span style="display:inline-flex;align-items:center;gap:5px;font-size:12px;'
                    'color:#27500A;background:#EAF3DE;border-radius:999px;padding:4px 10px;margin:0 4px 4px 0;">'
                    "✓ {name} +{w}</span>"
                ).format(name=name, w=crit.weight)
            else:
                missing += Markup(
                    '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;'
                    'background:#FCEBEB;border-radius:8px;margin-bottom:7px;">'
                    '<span style="color:#A32D2D;font-weight:500;">✕</span>'
                    '<span style="flex:1;font-size:13px;color:#501313;">{name}</span>'
                    '<span style="font-size:13px;font-weight:500;color:#A32D2D;">0 / {w}</span>'
                    "</div>"
                ).format(name=name, w=crit.weight)

        html = Markup("")
        if missing:
            html += Markup('<p style="font-weight:500;margin:0 0 8px;">Ce reduce vizibilitatea</p>') + missing
        if met:
            html += Markup('<p style="font-weight:500;margin:16px 0 8px;">Îndeplinit</p><div>') + met + Markup("</div>")
        if not html:
            html = Markup('<p style="color:#888780;">Nu există criterii active de vizibilitate.</p>')
        return html
