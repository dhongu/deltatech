odoo.define("deltatech_download.ActionManager", function (require) {
    "use strict";

    var ActionManager = require("web.ActionManager");

    ActionManager.include({
        _executeURLAction: function (action) {
            var result = this._super.apply(this, arguments);
            this._closeDialog({infos: action.infos});
            return result;
        },

        _triggerDownload: function (action, options, type) {
            var self = this;
            var reportUrls = this._makeReportUrls(action);
            if (type === "pdf") {
                var pdfWindow = window.open(reportUrls.pdf, "_blank");
                pdfWindow.document.title = "Download";
                if (action.close_on_report_download) {
                    var closeAction = {type: "ir.actions.act_window_close"};
                    return self.doAction(closeAction, _.pick(options, "on_close"));
                }
                return options.on_close();
            }
            return this._super.apply(this, arguments);
        },

        _executeReportAction: function (action, options) {
            var self = this;
            if (action.report_type === "pdf") {
                return self._triggerDownload(action, options, "pdf");
            }
            return this._super.apply(this, arguments);
        },
    });
});
