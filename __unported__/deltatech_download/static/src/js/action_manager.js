odoo.define("deltatech_download.ActionManager", function(require) {
    "use strict";

    var ActionManager = require("web.ActionManager");
    var session = require("web.session");
    var framework = require("web.framework");

    ActionManager.include({
        ir_actions_act_url: function(action, options) {
            var url = action.url;
            if (session.debug && url && url.length && url[0] === "/") {
                url = $.param.querystring(url, {debug: session.debug});
            }
            this.dialog_stop();
            if (action.target === "self") {
                framework.redirect(url);
                // The action is finished only when the redirection is done
                return $.Deferred();
            }
            window.open(url, "_blank");
            options.on_close();

            return $.when();
        },

        _triggerDownload: function(action, options, type) {
            var self = this;

            if (!type === "pdf") {
                this._super.apply(this, arguments);
            } else {
                var report_urls = this._makeReportUrls(action);
                var myWindow = window.open(report_urls.pdf, "_blank");
                myWindow.document.title = "Download";
                if (action.close_on_report_download) {
                    var closeAction = {type: "ir.actions.act_window_close"};
                    return self.doAction(closeAction, _.pick(options, "on_close"));
                }
                return options.on_close();
            }
        },
    });
});
