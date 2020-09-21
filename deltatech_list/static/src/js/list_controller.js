odoo.define("deltatech_list.ListController", function(require) {
    "use strict";

    var core = require("web.core");
    var ListController = require("web.ListController");

    var qweb = core.qweb;

    ListController.include({
        init: function(parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.SelectedIds = params.SelectedIds || [];
            this.legend = $($.parseHTML(parent.action.help)).filter("#legend");
            this.activeActions.info = Boolean(this.legend.length);
        },

        update: function(params, options) {
            var self = this;
            var data = this.model.get(this.handle).data;
            var res_ids = this.model.get(this.handle).res_ids;

            this.SelectedIds = this.getSelectedIds();
            params.SelectedIds = this.SelectedIds;

            return this._super.apply(this, arguments);
        },

        renderButtons: function($node) {
            this._super.apply(this, arguments);
            if (!this.noLeaf && this.hasButtons) {
                // This.$buttons = $(qweb.render('ListView.buttons', {widget: this}));
                this.$buttons.on("click", ".o_list_button_info", this._onInfo.bind(this));
            }
        },

        _onInfo: function(event) {
            var modal = $("#Info");

            var $info = $("#InfoBody");
            var $legend = this.legend;

            if ($legend && $info) {
                $("#InfoBody").empty();
                $("#InfoBody").append($legend.html());
            }
        },
    });
});
