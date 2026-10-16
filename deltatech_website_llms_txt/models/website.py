# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models

# Links listed per section: llms.txt is an index for a model's context, not a sitemap.
LLMS_TXT_LINK_LIMIT = 100


def _link_text(text):
    """Text of a Markdown link, on one line and without the brackets that would end it."""
    return " ".join((text or "").replace("[", "(").replace("]", ")").split())


class Website(models.Model):
    _inherit = "website"

    llms_txt_enabled = fields.Boolean(
        string="Publish llms.txt",
        default=True,
        help="Serve /llms.txt, the summary of the site that AI assistants read before its pages.",
    )
    llms_txt_summary = fields.Text(
        string="llms.txt Summary",
        help="One or two sentences on who you are and what you sell. "
        "Without it, the meta description of the homepage is used.",
    )
    llms_txt_details = fields.Text(
        string="llms.txt Details",
        help="Markdown added after the summary: delivery areas, payment, returns, "
        "what the assistants should know before recommending you.",
    )
    llms_txt_custom = fields.Text(
        string="Custom llms.txt",
        help="When filled in, served as is instead of the generated file.",
    )

    def _get_llms_txt(self):
        self.ensure_one()
        if self.llms_txt_custom and self.llms_txt_custom.strip():
            return self.llms_txt_custom.strip() + "\n"

        lines = [f"# {_link_text(self.name or self.company_id.name)}", ""]
        summary = (self.llms_txt_summary or self._get_llms_txt_default_summary() or "").strip()
        if summary:
            lines += [f"> {' '.join(summary.split())}", ""]
        contact = self._get_llms_txt_contact()
        if contact:
            lines += [contact, ""]
        if self.llms_txt_details and self.llms_txt_details.strip():
            lines += [self.llms_txt_details.strip(), ""]

        for title, links in self._get_llms_txt_sections():
            if not links:
                continue
            lines += [f"## {title}", ""]
            for name, url, note in links:
                line = f"- [{_link_text(name)}]({url})"
                if note:
                    line += f": {' '.join(note.split())}"
                lines.append(line)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _get_llms_txt_default_summary(self):
        homepage = self.with_context(website_id=self.id)._get_website_pages(domain=[("url", "=", "/")], limit=1)
        return homepage.website_meta_description

    def _get_llms_txt_contact(self):
        company = self.company_id
        parts = [value for value in (company.email, company.phone) if value]
        address = ", ".join(value for value in (company.city, company.country_id.name) if value)
        if address:
            parts.append(address)
        return f"Contact: {' · '.join(parts)}" if parts else ""

    def _get_llms_txt_sections(self):
        """List of (title, [(name, absolute url, note)]): other modules add their sections."""
        base_url = self.get_base_url()
        pages = self.with_context(website_id=self.id)._get_website_pages(
            domain=[("is_published", "=", True), ("website_indexed", "=", True)],
            order="url",
            limit=LLMS_TXT_LINK_LIMIT,
        )
        page_links = [(page.name, base_url + page.url, page.website_meta_description) for page in pages]
        sections = [(self.env._("Pages"), page_links)]
        # the shop is optional: the module only needs `website`
        if "product.public.category" in self.env:
            categories = (
                self.env["product.public.category"]
                .sudo()
                .search(self.website_domain(), order="parent_path", limit=LLMS_TXT_LINK_LIMIT)
            )
            slug = self.env["ir.http"]._slug
            shop_links = [(self.env._("Shop"), f"{base_url}/shop", "")]
            # sorted by path, so that subcategories follow their parent
            shop_links += [
                (category.display_name, f"{base_url}/shop/category/{slug(category)}", "")
                for category in categories.sorted("display_name")
            ]
            sections.append((self.env._("Shop"), shop_links))
        sections.append(("Optional", [(self.env._("Sitemap"), f"{base_url}/sitemap.xml", "")]))
        return sections
