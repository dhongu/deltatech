odoo.define("deltatech_website_snippets.s_category_list_frontend", function(require) {
    "use strict";

    var core = require("web.core");
    var sAnimation = require("website.content.snippets.animation");

    var _t = core._t;

    sAnimation.registry.js_get_category = sAnimation.Class.extend({
        selector: ".js_get_category",

        start: function() {
            var self = this;

            var template = self.$target.data("template") || "deltatech_website_snippets.s_category_list_template";
            var loading = self.$target.data("loading");
            var domain = [];

            this.$target.empty(); // Compatibility with db that saved content inside by mistake
            this.$target.attr("contenteditable", "False"); // Prevent user edition

            var def = $.Deferred();
            this._rpc({
                route: "/snipped/render_category_list",
                params: {
                    template: template,
                    domain: domain,
                },
            })
                .then(
                    function(categories) {
                        var $categories = $(categories); // .filter('.s_category_list');
                        if (!$categories.length) {
                            self.$target.append(
                                $("<div/>", {class: "col-md-6 offset-md-3"}).append(
                                    $("<div/>", {
                                        class: "alert alert-warning alert-dismissible text-center",
                                        text: _t("No  category was found. Make sure your category are published."),
                                    })
                                )
                            );
                            return;
                        }

                        self.$target.html(categories);
                    },
                    function(e) {
                        if (self.editableMode) {
                            self.$target.append(
                                $("<p/>", {
                                    class: "text-danger",
                                    text: _t(
                                        "An error occured with this latest posts block. If the problem persists, please consider deleting it and adding a new one"
                                    ),
                                })
                            );
                        }
                    }
                )
                .always(def.resolve.bind(def));
            return $.when(this._super.apply(this, arguments), def);
        },

        destroy: function() {
            this.$target.empty();
            this._super.apply(this, arguments);
        },

        _showLoading: function($categories) {
            var self = this;
        },
    });
});
