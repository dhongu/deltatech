# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response


class CustomerPortal(http.Controller):
    @http.route(['/my/purchase/<int:order_id>/update_price_note'], type='json', auth="public", website=True)
    def portal_my_purchase_order_update_price_note(self, order_id=None, access_token=None, **kw):
        """Allow the vendor to update price_unit and vendor_note on purchase order lines via portal.
        Expects payload keys like 'price_<line_id>' and 'note_<line_id>'.
        """
        try:
            order_sudo = request.env['purchase.order']._document_check_access(order_id, access_token=access_token)
        except AttributeError:
            # Fallback to controller helper if available on controller in older Odoo
            try:
                from odoo.addons.purchase.controllers.portal import CustomerPortal as PurchasePortal
                order_sudo = PurchasePortal()._document_check_access('purchase.order', order_id, access_token=access_token)
            except Exception:
                order_sudo = None
        except (AccessError, MissingError):
            return request.redirect('/my')

        if not order_sudo:
            # Last resort
            try:
                from odoo.addons.purchase.controllers.portal import CustomerPortal as PurchasePortal
                order_sudo = PurchasePortal()._document_check_access('purchase.order', order_id, access_token=access_token)
            except Exception:
                return request.redirect('/my')

        # Only allow editing when RFQ was sent (mirroring date edit behavior)
        if order_sudo.state != 'sent':
            return Response(status=403)

        # Build updates per line
        to_update = {}
        for key, val in kw.items():
            if key.startswith('price_'):
                try:
                    line_id = int(key.split('_', 1)[1])
                except Exception:
                    continue
                to_update.setdefault(line_id, {})['price_unit'] = float(val) if val not in (None, '') else 0.0
            elif key.startswith('name_'):
                try:
                    line_id = int(key.split('_', 1)[1])
                except Exception:
                    continue
                to_update.setdefault(line_id, {})['name'] = val
            elif key.startswith('note_'):
                try:
                    line_id = int(key.split('_', 1)[1])
                except Exception:
                    continue
                to_update.setdefault(line_id, {})['vendor_note'] = val

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
