/** @odoo-module **/

import {registry} from "@web/core/registry";
import config from "web.config";

async function pdfReportHandler(action, options, env) {
    if (config.device.isMobile) {
        return;
    }
    if (action.device_id) {
        // Raportul se va tipari prin IoT
        return;
    }
    if (action.direct_download) {
        // Raportul PDF trebuie descarcat standard
        return;
    }

    if (action.report_type === "qweb-pdf") {
        // && !action.direct_download) {

        const type = "pdf";
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
            if (type === "pdf") {
                const context = encodeURIComponent(JSON.stringify(env.services.user.context));
                url_ += `?context=${context}`;
            }
        }
        // COPY actionManager._triggerDownload
        env.services.ui.block();
        try {
            var pdfWindow = window.open(url_, "_blank");
            pdfWindow.document.title = "Download";
        } finally {
            env.services.ui.unblock();
        }
        const onClose = options.onClose;
        if (action.close_on_report_download) {
            env.services.action.doAction({type: "ir.actions.act_window_close"}, {onClose});
            return true;
        } else if (onClose) {
            onClose();
        }
        // DIFF: need to inform success to the original method. Otherwise it
        // will think our hook function did nothing and run the original
        // method.
        // return Promise.resolve(true);
        return true;
    }
}

registry.category("ir.actions.report handlers").add("pdf_handler", pdfReportHandler);
