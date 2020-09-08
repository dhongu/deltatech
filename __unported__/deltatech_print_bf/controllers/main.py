# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import werkzeug.utils
import werkzeug.wrappers

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import binary_content
from odoo.http import content_disposition
import base64
from odoo.http import request


class Binary(http.Controller):

    @http.route(['/web/binary/download_document'], type='http', auth="public")
    def download_document(self, xmlid=None, model='ir.attachment', id=None, field='datas', filename=None,
                          filename_field='datas_fname', unique=None, mimetype=None, download=None, data=None, token=None, debug=None):
        status, headers, content = binary_content(xmlid=xmlid, model=model, id=id, field=field, unique=unique,
                                                  filename=filename, filename_field=filename_field, download=download, mimetype=mimetype)
        if status == 304:
            response = werkzeug.wrappers.Response(status=status, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            response = request.not_found()
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            headers.append(('Content-Type', 'application/octet-stream'))
            headers.append(('Content-Disposition', content_disposition(filename)))

            response = request.make_response(content_base64, headers)
        if token:
            response.set_cookie('fileToken', token)
        return response


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
