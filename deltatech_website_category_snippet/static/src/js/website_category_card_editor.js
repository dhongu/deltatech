odoo.define("deltatech_website_category_snippet.category_card_editor", function (require) {
    "use strict";

    var core = require("web.core");

    var wUtils = require("website.utils");
    var options = require("web_editor.snippets.options");

    var _t = core._t;

    options.registry.edit_category_card = options.Class.extend({
        select_category: function () {
            var self = this;
            return wUtils
                .prompt({
                    id: "editor_category_card",
                    window_title: _t("Select a Category"),
                    select: _t("Category"),
                    init: function () {
                        return self._rpc({
                            model: "product.public.category",
                            method: "name_search",
                            args: ["", []],
                        });
                    },
                })
                .then(function (result) {
                    self.$target.attr("data-id", result.val);
                });
        },
        onBuilt: function () {
            var self = this;
            this._super();
            this.select_category("click").guardedCatch(function () {
                self.getParent().removeSnippet();
            });
        },
        cleanForSave: function () {
            this.$target.addClass("d-none");
        },
    });
});
