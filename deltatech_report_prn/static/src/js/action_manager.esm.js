/** @odoo-module **/
import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";

// Build the internal report url for a qweb-prn report action. Exported so
// companion modules (e.g. a Zebra Browser Print add-on) can fetch the rendered
// ZPL/PRN text from the same route instead of downloading it.
export function buildPrnUrl(action) {
    let url_ = `/report/prn/${action.report_name}`;
    const actionContext = action.context || {};
    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options_ = encodeURIComponent(JSON.stringify(action.data));
        const context_ = encodeURIComponent(JSON.stringify(actionContext));
        url_ += `?options=${options_}&context=${context_}`;
    } else {
        if (actionContext.active_ids) {
            url_ += `/${actionContext.active_ids.join(",")}`;
        }
        const context = encodeURIComponent(JSON.stringify(action.context));
        url_ += `?context=${context}`;
    }
    return url_;
}

async function prnReportHandler(action, options, env) {
    if (action.device_id) {
        // The report is printed through IoT, handled elsewhere.
        return;
    }
    if (action.report_type !== "qweb-prn") {
        return;
    }
    // Legacy flow: download the .prn file. On the workstation the .prn file
    // extension is associated with a .bat script that forwards it to the
    // printer. A companion module may intercept this report earlier (lower
    // sequence) to print through Zebra Browser Print and only fall back here.
    const url_ = buildPrnUrl(action);
    env.services.ui.block();
    try {
        await download({
            url: "/report/download",
            data: {
                data: JSON.stringify([url_, action.report_type]),
                context: JSON.stringify(action.context),
            },
        });
    } finally {
        env.services.ui.unblock();
    }
    // Returning a truthy value tells the action service this report was
    // handled; it takes care of close_on_report_download / onClose.
    return true;
}

registry.category("ir.actions.report handlers").add("prn_handler", prnReportHandler);
