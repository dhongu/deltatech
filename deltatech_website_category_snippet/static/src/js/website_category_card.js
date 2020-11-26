odoo.define("deltatech_website_category_snippet.category_card", function (require) {
    "use strict";

    var concurrency = require("web.concurrency");

    var core = require("web.core");
    var publicWidget = require("web.public.widget");

    var qweb = core.qweb;

    publicWidget.registry.categoryCardSnippet = publicWidget.Widget.extend({
        selector: ".s_wsale_category_card",
        xmlDependencies: ["/deltatech_website_category_snippet/static/src/xml/website_category_card.xml"],
        disabledInEditableMode: false,

        /**
         * @class
         */
        init: function () {
            this._super.apply(this, arguments);
            this._dp = new concurrency.DropPrevious();
            this.uniqueId = _.uniqueId("o_category_list_card_");
            this._onResizeChange = _.debounce(this._addList, 100);
        },
        /**
         * @override
         */
        start: function () {
            this._dp.add(this._fetch()).then(this._render.bind(this));
            $(window).resize(() => {
                this._onResizeChange();
            });
            return this._super.apply(this, arguments);
        },
        /**
         * @override
         */
        destroy: function () {
            this._super(...arguments);
            this.$el.addClass("d-none");
            this.$el.find(".subcategory_list").html("");
        },

        _fetch: function () {
            return this._rpc({
                route: "/shop/category/card",
                params: {
                    category_id: this.$target.data("id"),
                },
            }).then((res) => {
                var categories = res.categories;

                // In edit mode, if the current visitor has no recently viewed
                // categories, use demo data.
                if (this.editableMode && (!categories || !categories.length)) {
                    return {
                        categories: [
                            {
                                id: 0,
                                website_url: "#",
                                display_name: "Categ 1",
                                image: "/deltatech/deltatech_website_category_snippet/static/src/img/categ1.jpg",
                            },
                            {
                                id: 0,
                                website_url: "#",
                                display_name: "Categ 2",
                                image: "//deltatech/deltatech_website_category_snippet/static/src/img/categ2.jpg",
                            },
                        ],
                    };
                }

                return res;
            });
        },

        _render: function (res) {
            var categories = res.categories;

            this.webList = $(
                qweb.render("deltatech_website_category_snippet.categoryCard", {
                    uniqueId: this.uniqueId,
                    categories: categories,
                })
            );
            this._addList();
            this.$el.toggleClass("d-none", !(categories && categories.length));
        },
        /**
         * Add the right carousel depending on screen size.
         * @private
         */
        _addList: function () {
            this.$(".subcategory_list").html(this.webList).css("display", "");
        },
    });
});
