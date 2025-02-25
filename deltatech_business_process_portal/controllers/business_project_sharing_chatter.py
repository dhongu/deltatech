# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug.exceptions import Forbidden

from odoo.http import route

from odoo.addons.portal.controllers.mail import PortalChatter

from .portal import BusinessProcesssPortal


class BusinessProcessSharingChatter(PortalChatter):
    def _check_business_project_access_and_get_token(self, res_model, res_id, token):
        if not token or token == "null":
            business_project_sudo = BusinessProcesssPortal._document_check_access(self, res_model, res_id, token)
            can_access = business_project_sudo
            if not can_access:
                raise Forbidden()
            token = business_project_sudo[business_project_sudo._mail_post_token_field]
            if not token or token == "null":
                business_project_sudo._portal_ensure_token()
                token = business_project_sudo[business_project_sudo._mail_post_token_field]
            return token
        return token

    @route()
    def portal_chatter_init(self, res_model, res_id, domain=False, limit=False, **kwargs):
        token = self._check_business_project_access_and_get_token(res_model, res_id, kwargs.get("token"))
        if token:
            kwargs["token"] = token
        return super().portal_chatter_init(res_model, res_id, domain=domain, limit=limit, **kwargs)

    @route()
    def portal_chatter_post(self, res_model, res_id, message, attachment_ids=None, attachment_tokens=None, **kwargs):
        token = self._check_business_project_access_and_get_token(res_model, res_id, kwargs.get("token"))
        if token:
            kwargs["token"] = token
        return super().portal_chatter_post(
            res_model, res_id, message, attachment_ids=attachment_ids, attachment_tokens=attachment_tokens, **kwargs
        )

    @route()
    def portal_message_fetch(self, res_model, res_id, domain=False, limit=10, offset=0, **kwargs):
        token = self._check_business_project_access_and_get_token(res_model, res_id, kwargs.get("token"))
        if token:
            kwargs["token"] = token
        return super().portal_message_fetch(res_model, res_id, domain=domain, limit=limit, offset=offset, **kwargs)
