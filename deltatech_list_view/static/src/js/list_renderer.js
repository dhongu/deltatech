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

    // Todo: da facut un modul separat
    var relational_fields = require("web.relational_fields");
    var FieldMany2One = relational_fields.FieldMany2One;

    FieldMany2One.include({
        init: function () {
            this._super.apply(this, arguments);

            this.nodeOptions = _.defaults(this.nodeOptions, {
                quick_create: false,
                no_quick_create: true,
            });
        },

        _search: async function (searchValue = "") {
            var self = this;
            var values = await this._super.apply(this, arguments);

            if (self.limit >= values.length) {
                const value = searchValue.trim();
                const domain = self.record.getDomain(self.recordParams);
                const context = Object.assign(self.record.getContext(self.recordParams), self.additionalContext);
                values = self._manageSearchMore(values, value, domain, context);
            }

            return values;
        },
    });
});
