odoo.define("deltatech_list.ListController", function (require) {
    "use strict";

    var core = require("web.core");
    var ListController = require("web.ListController");

    var QWeb = core.qweb;

    ListController.include({
        init: function (parent, model, renderer, params) {
            this.context = renderer.state.getContext();
            this._super.apply(this, arguments);
            this.SelectedIds = params.SelectedIds || [];
            this.legend = "";
            if (renderer.noContentHelp) {
                this.legend = $($.parseHTML(renderer.noContentHelp)).filter("#legend");
            }

            this.headerGeneralButtons = this.context.general_buttons || [];

            this.modelName = params.modelName;
            this.hasLegend = Boolean(this.legend.length);
            this.activeActions.info = Boolean(this.legend.length);
        },

        update: function (params) {
            this.SelectedIds = this.getSelectedIds();
            params.SelectedIds = this.SelectedIds;
            return this._super.apply(this, arguments);
        },

        renderButtons: function () {
            this._super.apply(this, arguments);
            if (!this.noLeaf && this.hasButtons) {
                this.$buttons.on("click", ".o_list_button_legend", this._onShowLegend.bind(this));
            }
            if (this.headerGeneralButtons) {
                this.$generalButtons = $(QWeb.render("ListView.GeneralButtons", {buttons: this.headerGeneralButtons}));
                this.$buttons.on("click", ".o_general_button", this._onClickGeneralButton.bind(this));
                this.$buttons.prepend(this.$generalButtons);
            }
        },

        _onClickGeneralButton: function (event) {
            var el = event.target;
            var self = this;
            self._rpc({
                model: $(el).attr("model") || self.modelName,
                method: $(el).attr("action"),
                args: [self.context.active_id],
                context: self.context,
            }).then(function (result) {
                return self.do_action(result);
            });
        },

        _onShowLegend: function () {
            var $legend_body = $("#LegendBody");
            var $legend = this.legend;

            if ($legend && $legend_body) {
                $legend_body.empty();
                $legend_body.append($legend.html());
            }
        },
    });
});
