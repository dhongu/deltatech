odoo.define("deltatech_download.ActionManager", function (require) {
    "use strict";

    var ActionManager = require("web.ActionManager");
    var core = require("web.core");
    var _t = core._t;

    ActionManager.include({
        _executeURLAction: function (action) {
            var result = this._super.apply(this, arguments);
            this._closeDialog({infos: action.infos});
            return result;
        },

        _triggerDownload: function (action, options, type) {
            var self = this;
            var reportUrls = this._makeReportUrls(action);
            if (type === "pdf" && !action.direct_download) {
                return this._openReportPDF(reportUrls[type]).then(function () {
                    if (action.close_on_report_download) {
                        var closeAction = {type: "ir.actions.act_window_close"};
                        return self.doAction(closeAction, _.pick(options, "on_close"));
                    }
                    return options.on_close();
                });
            }
            return this._super.apply(this, arguments);
        },

        _openReportPDF: function (url) {
            var def = $.Deferred();

            if (!window.open(url)) {
                // AAB: this check should be done in get_file service directly,
                // should not be the concern of the caller (and that way, get_file
                // could return a deferred)
                var message = _t(
                    "A popup window with your report was blocked. You " +
                        "may need to change your browser settings to allow " +
                        "popup windows for this page."
                );
                this.do_warn(_t("Warning"), message, true);
            }

            return def;
        },
    });
});
