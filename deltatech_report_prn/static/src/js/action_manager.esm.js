/** @odoo-module **/

import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import config from "web.config";

async function prnReportHandler(action, options, env) {
    if (config.device.isMobile) {
        return;
    }
    if (action.report_type === "qweb-prn") {
        const type = "prn";
        // COPY actionManager._getReportUrl
        let url_ = `/report/${type}/${action.report_name}`;
        const actionContext = action.context || {};
        if (action.data && JSON.stringify(action.data) !== "{}") {
            // Build a query string with `action.data` (it's the place where reports
            // using a wizard to customize the output traditionally put their options)
            const options_ = encodeURIComponent(JSON.stringify(action.data));
            const context_ = encodeURIComponent(JSON.stringify(actionContext));
            url_ += `?options=${options_}&context=${context_}`;
        } else {
            if (actionContext.active_ids) {
                url_ += `/${actionContext.active_ids.join(",")}`;
            }
            if (type === "prn") {
                const context = encodeURIComponent(JSON.stringify(env.services.user.context));
                url_ += `?context=${context}`;
            }
        }
        // COPY actionManager._triggerDownload
        env.services.ui.block();
        try {
            await download({
                url: "/report/download",
                data: {
                    data: JSON.stringify([url_, action.report_type]),
                    context: JSON.stringify(env.services.user.context),
                },
            });
        } finally {
            env.services.ui.unblock();
        }
        const onClose = options.onClose;
        if (action.close_on_report_download) {
            return env.services.action.doAction({type: "ir.actions.act_window_close"}, {onClose});
        } else if (onClose) {
            onClose();
        }
        // DIFF: need to inform success to the original method. Otherwise it
        // will think our hook function did nothing and run the original
        // method.
        return Promise.resolve(true);
    }
}

registry.category("ir.actions.report handlers").add("prn_handler", prnReportHandler);

// Odoo.define("deltatech_report_prn.ActionManager", function (require) {
//     "use strict";
//
//     var ActionManager = require("web.ActionManager");
//
//     ActionManager.include({
//         _executeReportAction: function (action, options) {
//             var self = this;
//             if (action.report_type === "qweb-prn") {
//                 return self._triggerDownload(action, options, "prn");
//             }
//             return this._super.apply(this, arguments);
//         },
//
//         _makeReportUrls: function () {
//             var reportUrls = this._super.apply(this, arguments);
//             reportUrls.prn = reportUrls.text.replace("/report/text/", "/report/prn/");
//             return reportUrls;
//         },
//     });
// });
