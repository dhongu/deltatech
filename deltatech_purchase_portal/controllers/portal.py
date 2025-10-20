# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import binascii

from odoo import _, fields, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import Response, request

from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.purchase.controllers.portal import CustomerPortal as PurchasePortal


class VendorPurchasePortal(PurchasePortal):
    @http.route(["/my/purchase/<int:order_id>/update_price_note"], type="json", auth="public", website=True)
    def portal_my_purchase_order_update_price_note(self, order_id=None, access_token=None, **kw):
        """Allow the vendor to update price_unit and vendor_note on purchase order lines via portal.
        Expects payload keys like 'price_<line_id>' and 'note_<line_id>'.
        """
        try:
            order_sudo = self._document_check_access("purchase.order", order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")

        # Only allow editing when RFQ was sent (mirroring date edit behavior)
        if order_sudo.state != "sent":
            return Response(status=403)

        # Build updates per line
        to_update = {}
        for key, val in kw.items():
            if key.startswith("price_"):
                try:
                    line_id = int(key.split("_", 1)[1])
                except Exception:
                    continue
                to_update.setdefault(line_id, {})["price_unit"] = float(val) if val not in (None, "") else 0.0
            elif key.startswith("name_"):
                try:
                    line_id = int(key.split("_", 1)[1])
                except Exception:
                    continue
                to_update.setdefault(line_id, {})["name"] = val
            elif key.startswith("note_"):
                try:
                    line_id = int(key.split("_", 1)[1])
                except Exception:
                    continue
                to_update.setdefault(line_id, {})["vendor_note"] = val

        if not to_update:
            return Response(status=204)

        lines = order_sudo.order_line.filtered(lambda l: l.id in to_update.keys())
        for line in lines:
            vals = to_update.get(line.id, {})
            # Do not allow editing display lines
            if line.display_type:
                continue
            # Write with sudo of record env
            line.sudo().write(vals)

        return Response(status=204)

    @http.route(["/my/purchase/<int:order_id>/accept"], type="json", auth="public", website=True)
    def portal_rfq_accept(self, order_id, access_token=None, name=None, signature=None):
        """Accept & Sign RFQ like sales order signing.
        Writes signed_by, signed_on, signature; then confirms the RFQ.
        Returns a redirect to the RFQ portal page with a success message.
        """
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get("access_token")
        try:
            order_sudo = self._document_check_access("purchase.order", order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {"error": _("Invalid RFQ.")}

        if order_sudo.state != "sent":
            return {"error": _("The RFQ is not in a state requiring vendor signature.")}
        if not signature:
            return {"error": _("Signature is missing.")}

        try:
            order_sudo.sudo().write(
                {
                    "signed_by": name,
                    "signed_on": fields.Datetime.now(),
                    "signature": signature,
                }
            )
            # flush now to make signature data available to PDF render request
            request.env.cr.flush()
        except (TypeError, binascii.Error):
            return {"error": _("Invalid signature data.")}

        # Confirm RFQ to Purchase Order
        if order_sudo.state == "sent":
            order_sudo.with_context(send_email=True).button_confirm()

        # Generate PDF and post message in chatter
        pdf = (
            request.env["ir.actions.report"]
            .sudo()
            ._render_qweb_pdf("purchase.action_report_purchase_order", [order_sudo.id])[0]
        )
        _message_post_helper(
            "purchase.order",
            order_sudo.id,
            _("RFQ signed by %s", name),
            attachments=[(f"{order_sudo.name}.pdf", pdf)],
            token=access_token,
        )

        query_string = "&message=sign_ok"
        return {
            "force_refresh": True,
            "redirect_url": order_sudo.get_portal_url(query_string=query_string),
        }

    # Legacy simple sign route kept for backward compatibility (no-op when already implemented above)
    @http.route(["/my/purchase/<int:order_id>/vendor_sign"], type="http", auth="public", website=True)
    def portal_my_purchase_order_vendor_sign(self, order_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access("purchase.order", order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")
        return request.redirect(order_sudo.get_portal_url())
