/** @odoo-module **/
import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {_t} from "@web/core/l10n/translation";

// The selected printer is persisted per workstation (localStorage), never per
// user: the device uid is machine-specific and would break when the same user
// prints from another computer. See readme/ROADMAP.md (Phase 2).
const PRINTER_UID_KEY = "deltatech_zebra_printer_uid";

function buildPrnUrl(action) {
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

async function downloadPrn(action, env) {
    // Legacy flow: download the .prn file. On the workstation the .prn file
    // extension is associated with a .bat script that forwards it to the
    // printer.
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
}

function isBrowserPrintAvailable() {
    // The proprietary Zebra Browser Print SDK is provided by a separate
    // (private) companion module that loads it through web.assets_backend, so
    // it exposes the global `window.BrowserPrint`. This module keeps no
    // reference to that SDK: when no companion is installed the global is
    // absent and we fall back to the legacy .prn download.
    return Boolean(window.BrowserPrint);
}

function getDefaultDevice() {
    return new Promise((resolve) => {
        try {
            window.BrowserPrint.getDefaultDevice(
                "printer",
                (device) => resolve(device || null),
                () => resolve(null)
            );
        } catch {
            resolve(null);
        }
    });
}

function getLocalDevices() {
    return new Promise((resolve) => {
        try {
            window.BrowserPrint.getLocalDevices(
                (devices) => resolve(devices || []),
                () => resolve([]),
                "printer"
            );
        } catch {
            resolve([]);
        }
    });
}

async function resolvePrinter() {
    const devices = await getLocalDevices();
    if (!devices.length) {
        return null;
    }
    // 1. Selection saved on THIS workstation.
    const savedUid = window.localStorage.getItem(PRINTER_UID_KEY);
    if (savedUid) {
        const match = devices.find((d) => d.uid === savedUid);
        if (match) {
            return match;
        }
    }
    // 2. Default device configured once per machine in the Browser Print app.
    const def = await getDefaultDevice();
    if (def) {
        return def;
    }
    // 3. Exactly one printer: use it.
    if (devices.length === 1) {
        return devices[0];
    }
    // 4. Ambiguous (several printers, nothing saved/default). The picker dialog
    // is Phase 2; until then we do not guess and let the caller fall back.
    return null;
}

function sendToPrinter(device, data) {
    return new Promise((resolve, reject) => {
        try {
            device.send(
                data,
                () => resolve(true),
                (err) => reject(new Error(err || "Browser Print send failed"))
            );
        } catch (err) {
            reject(err);
        }
    });
}

async function tryBrowserPrint(action, env) {
    if (!isBrowserPrintAvailable()) {
        return false;
    }
    const device = await resolvePrinter();
    if (!device) {
        return false;
    }
    // Fetch the rendered ZPL/PRN text (same route the legacy flow downloads).
    const response = await fetch(buildPrnUrl(action), {credentials: "same-origin"});
    if (!response.ok) {
        return false;
    }
    const zpl = await response.text();
    await sendToPrinter(device, zpl);
    if (device.uid) {
        window.localStorage.setItem(PRINTER_UID_KEY, device.uid);
    }
    const message = _t("Label sent to printer:") + " " + (device.name || "");
    env.services.notification.add(message, {type: "success"});
    return true;
}

async function prnReportHandler(action, options, env) {
    if (action.device_id) {
        // The report is printed through IoT, handled elsewhere.
        return;
    }
    if (action.report_type !== "qweb-prn") {
        return;
    }

    let printed = false;
    if (session.deltatech_browser_print_enabled) {
        try {
            printed = await tryBrowserPrint(action, env);
        } catch (err) {
            // Any Browser Print failure falls back to the legacy .prn download,
            // so mixed fleets (workstations without Browser Print installed)
            // keep working.
            console.warn("Zebra Browser Print failed, falling back to .prn download", err);
            env.services.notification.add(_t("Zebra Browser Print failed, downloading .prn instead."), {
                type: "warning",
            });
            printed = false;
        }
    }

    if (!printed) {
        await downloadPrn(action, env);
    }

    const onClose = options.onClose;
    if (action.close_on_report_download) {
        return env.services.action.doAction({type: "ir.actions.act_window_close"}, {onClose});
    } else if (onClose) {
        onClose();
    }
    // Inform the action manager that this handler took care of the report.
    return Promise.resolve(true);
}

registry.category("ir.actions.report handlers").add("prn_handler", prnReportHandler);
