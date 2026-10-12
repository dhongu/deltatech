/* @odoo-module */

import {ListRenderer} from "@web/views/list/list_renderer";
import {patch} from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
    onCellClicked() {
        // Nu deschide înregistrarea când utilizatorul selectează text din celulă
        if (this.getSelectedText() === "") {
            return super.onCellClicked(...arguments);
        }
    },

    getSelectedText() {
        if (window.getSelection) {
            return window.getSelection().toString();
        } else if (document.selection) {
            return document.selection.createRange().text;
        }
        return "";
    },
});
