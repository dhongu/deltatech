odoo.define("deltatech_report_prn.ActionManager", function (require) {
    "use strict";

    var ActionManager = require("web.ActionManager");

    ActionManager.include({
        _executeReportAction: function (action, options) {
            var self = this;
            if (action.report_type === "qweb-prn") {
                return self._triggerDownload(action, options, "prn");
            }
            return this._super.apply(this, arguments);
        },

        _makeReportUrls: function () {
            var reportUrls = this._super.apply(this, arguments);
            reportUrls.prn = reportUrls.text.replace("/report/text/", "/report/prn/");
            return reportUrls;
        },
    });
});
