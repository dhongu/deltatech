odoo.define("deltatech_list.ListRenderer", function (require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");

    ListRenderer.include({
        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.selectionIds = params.SelectedIds || [];
        },

        updateState: function (state, params) {
            if (params.SelectedIds) {
                this.selectionIds = params.SelectedIds;
            }
            return this._super.apply(this, arguments);
        },

        _renderRow: function (record) {
            var $tr = this._super.apply(this, arguments);
            $tr.data("res_id", record.res_id);
            return $tr;
        },

        async _renderView() {
            await this._super(...arguments);

            var self = this;

            if (this.selectionIds.length) {
                // Self.updateSelection(this.selectionIds);
                var $checked_rows = this.$("tr").filter(function (index, el) {
                    var res = _.contains(self.selectionIds, $(el).data("res_id"));
                    if (res) {
                        $(el).find(".o_list_record_selector input").prop("checked", true);
                        self.selection.push($(el).data("id"));
                    }
                    return res;
                });
                $checked_rows.find(".o_list_record_selector input").prop("checked", true);
            }
        },
    });
});
