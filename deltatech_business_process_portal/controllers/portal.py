# ©  2023 Deltatech
# ©  2025 NextERP Romania
# See README.rst file on addons root folder for license details

from odoo import _, conf, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class BusinessProcesssPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if "business_project_count" in counters:
            values["business_project_count"] = (
                request.env["business.project"].search_count([])
                if request.env["business.project"].check_access_rights("read", raise_exception=False)
                else 0
            )
        return values

    def _business_project_get_page_view_values(
        self,
        business_project,
        access_token,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        search=None,
        search_in="content",
        groupby=None,
        **kwargs,
    ):
        values = {
            "page_name": business_project.name,
            "business_project": business_project,
        }
        if not groupby:
            values["groupby"] = "none"
        res = self._get_page_view_values(
            business_project,
            access_token,
            values,
            "my_business_projects_history",
            False,
            **kwargs,
        )

        return res

    def _get_business_projects_domain(self, partner):
        return [
            "|",
            "|",
            ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ("customer_id", "=", partner.id),
            ("customer_id", "child_of", [partner.commercial_partner_id.id]),
        ]

    def current_user(self):
        return request.env.user

    def _get_business_project_searchbar_sortings(self):
        return {
            "name": {"label": _("Data"), "order": "id desc"},
            "state": {"label": _("Status"), "order": "state"},
        }

    @http.route(
        ["/my/business_projects", "/my/business_projects/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_business_projects(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in="content",
        **kw,
    ):
        values = self._prepare_my_business_projects_values(page, date_begin, date_end, sortby, filterby)

        # pager
        pager = portal_pager(**values["pager"])

        # content according to pager and archive selected
        business_projects = values["business_projects"](pager["offset"])
        request.session["my_business_projects_history"] = business_projects.ids[:100]

        values.update(
            {
                "business_projects": business_projects,
                "pager": pager,
            }
        )
        res = request.render("deltatech_business_process_portal.portal_my_business_projects", values)
        return res

    def _prepare_my_business_projects_values(
        self,
        page,
        date_begin,
        date_end,
        sortby,
        domain=None,
        url="/my/business_projects",
    ):
        values = self._prepare_portal_layout_values()
        BusinessProcess = request.env["business.project"]
        partner = request.env.user.partner_id
        domain = expression.AND(
            [
                domain or [],
                self._get_business_projects_domain(partner),
            ]
        )

        searchbar_sortings = self._get_business_project_searchbar_sortings()
        # default sort by order
        if not sortby:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]
        values.update(
            {
                "date": date_begin,
                "business_projects": lambda pager_offset: BusinessProcess.search(
                    domain, order=order, limit=self._items_per_page, offset=pager_offset
                ),
                "page_name": "business_projects",
                "pager": {  # vals to define the pager.
                    "url": url,
                    "url_args": {
                        "date_begin": date_begin,
                        "date_end": date_end,
                        "sortby": sortby,
                    },
                    "total": BusinessProcess.search_count(domain),
                    "page": page,
                    "step": self._items_per_page,
                },
                "default_url": url,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return values

    @http.route(
        "/my/business_projects/<int:business_project_id>",
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_business_project_detail(self, business_project_id, access_token=None, **kw):
        try:
            business_project_sudo = self._document_check_access("business.project", business_project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")
        if not business_project_sudo.access_token:
            business_project_sudo._portal_ensure_token()
        # logo attachemnt
        logo_attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", business_project_sudo._name),
                    ("res_field", "=", "logo"),
                    ("res_id", "in", business_project_sudo.ids),
                ]
            )
        )
        if logo_attachment:
            logo_attachment.generate_access_token()
        business_project_sudo.attachment_ids.generate_access_token()
        values = {"business_project_id": business_project_id}
        res = request.render("deltatech_business_process_portal.business_project_sharing_portal", values)
        return res

    # incercare cu sharing
    def _prepare_business_project_sharing_session_info(self, business_project):
        session_info = request.env["ir.http"].session_info()
        user_context = dict(request.env.context) if request.session.uid else {}
        mods = conf.server_wide_modules or []
        if request.env.lang:
            lang = request.env.lang
            session_info["user_context"]["lang"] = lang
            # Update Cache
            user_context["lang"] = lang
        lang = user_context.get("lang")
        translation_hash = request.env["ir.http"].get_web_translations_hash(mods, lang)
        cache_hashes = {
            "translations": translation_hash,
        }
        current_company = request.env.company
        act_name = "deltatech_business_process_portal.action_business_project_sharing_form_action"
        session_info.update(
            cache_hashes=cache_hashes,
            action_name=act_name,
            active_id=business_project.id,
            business_project_id=business_project.id,
            user_companies={
                "current_company": current_company.id,
                "allowed_companies": {
                    current_company.id: {
                        "id": current_company.id,
                        "name": current_company.name,
                    },
                },
            },
            currencies=request.env["ir.http"].get_currencies(),
        )
        if business_project:
            session_info["open_business_project_action"] = business_project.action_business_project_sharing_open()

        return session_info

    @http.route(
        "/my/business_projects/<int:business_project_id>/business_project_sharing",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def render_business_project_backend_view(self, business_project_id):

        business_project_sudo = request.env["business.project"].sudo().browse(business_project_id)

        if not business_project_sudo.exists():
            return request.not_found()
        if not business_project_sudo.access_token:
            business_project_sudo._portal_ensure_token()
        # logo attachemnt
        logo_attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", business_project_sudo._name),
                    ("res_field", "=", "logo"),
                    ("res_id", "in", business_project_sudo.ids),
                ]
            )
        )
        if logo_attachment:
            logo_attachment.generate_access_token()
        business_project_sudo.attachment_ids.generate_access_token()
        session_info = self._prepare_business_project_sharing_session_info(business_project_sudo)
        result = request.render(
            "deltatech_business_process_portal.business_project_sharing_embed",
            {"session_info": session_info},
        )
        return result
