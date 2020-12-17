# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


import json
import time

from werkzeug.urls import url_decode

from odoo.http import content_disposition, request, route
from odoo.tools.safe_eval import safe_eval

from odoo.addons.web.controllers import main as report


class ReportController(report.ReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "prn":
            return super(ReportController, self).report_routes(reportname, docids, "text", **data)
        return super(ReportController, self).report_routes(reportname, docids, converter, **data)

    @route()
    def report_download(self, data, token, context=None):
        """This function is used by 'action_manager_report.js' in order to trigger the download of
        a pdf/controller report.

        :param data: a javascript array JSON.stringified containg report internal url ([0]) and
        type [1]
        :returns: Response with a filetoken cookie and an attachment header
        """

        requestcontent = json.loads(data)
        url, report_type = requestcontent[0], requestcontent[1]
        if report_type == "qweb-prn":
            converter = "prn"
            extension = "prn"

            pattern = "/report/prn/"
            reportname = url.split(pattern)[1].split("?")[0]

            docids = None
            if "/" in reportname:
                reportname, docids = reportname.split("/")

            if docids:
                # Generic report:
                response = self.report_routes(reportname, docids=docids, converter=converter, context=context)
            else:
                # Particular report:
                data = dict(url_decode(url.split("?")[1]).items())  # decoding the args represented in JSON
                if "context" in data:
                    context, data_context = json.loads(context or "{}"), json.loads(data.pop("context"))
                    context = json.dumps({**context, **data_context})
                response = self.report_routes(reportname, converter=converter, context=context, **data)

            report = request.env["ir.actions.report"]._get_report_from_name(reportname)
            filename = "{}.{}".format(report.name, extension)

            if docids:
                ids = [int(x) for x in docids.split(",")]
                obj = request.env[report.model].browse(ids)
                if report.print_report_name and not len(obj) > 1:
                    report_name = safe_eval(report.print_report_name, {"object": obj, "time": time})
                    filename = "{}.{}".format(report_name, extension)
            response.headers.add("Content-Disposition", content_disposition(filename))
            response.set_cookie("fileToken", token)
            return response

        return super(ReportController, self).report_download(data, token, context)
