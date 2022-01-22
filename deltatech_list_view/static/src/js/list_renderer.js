odoo.define("deltatech_list_view.ListRenderer", function (require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");

    ListRenderer.include({
        _onRowClicked: function () {
            if (this.getSelectedText() === "") {
                this._super.apply(this, arguments);
            }
        },

        getSelectedText: function () {
            if (window.getSelection) {
                return window.getSelection().toString();
            } else if (document.selection) {
                return document.selection.createRange().text;
            }
            return "";
        },
    });
});
