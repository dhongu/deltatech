/** @odoo-module */

import {ErrorDialog} from "@web/core/errors/error_dialogs";
import {session} from "@web/session";
import {browser} from "@web/core/browser/browser";

ErrorDialog.prototype.onClickOpenTicket = function () {
    console.log("onClickOpenTicket");
    const url = session.support_url;
    browser.open(url, "_blank");
};
