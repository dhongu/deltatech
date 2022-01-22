odoo.define("deltatech_website_product_slider_snippet.product_slider", function (require) {
    "use strict";

    const publicWidget = require("web.public.widget");
    const DynamicSnippetCarousel = require("website.s_dynamic_snippet_carousel");

    const SnippetProductsSlider = DynamicSnippetCarousel.extend({
        selector: ".s_snippet_products_slider",

        _isConfigComplete: function () {
            return this._super.apply(this, arguments) && this.$el.get(0).dataset.productListId !== undefined;
        },

        _mustMessageWarningBeHidden: function () {
            const isInitialDrop = this.$el.get(0).dataset.templateKey === undefined;
            // This snippet has default values obtained after the initial start and render after drop.
            // Because of this there is an initial refresh happening right after.
            // We want to avoid showing the incomplete config message before this refresh.
            // Since the refreshed call will always happen with a defined templateKey,
            // if it is not set yet, we know it is the drop call and we can avoid showing the message.
            return isInitialDrop || this._super.apply(this, arguments);
        },

        willStart: function () {
            return this._getDomain().then(this._super.bind(this));
        },

        _getDomain: function () {
            var self = this;
            const productListId = parseInt(this.$el.get(0).dataset.productListId, 10);
            return this._rpc({
                model: "product.list",
                method: "read",
                args: [productListId, ["products_domain"]],
            }).then(function (result) {
                if (result.length > 0) {
                    self.domain = JSON.parse(result[0].products_domain)[0];
                }
                return Promise.resolve();
            });
        },

        _getSearchDomain: function () {
            const searchDomain = this._super.apply(this, arguments);
            if (this.domain) {
                searchDomain.push(this.domain);
            }
            return searchDomain;
        },
    });
    publicWidget.registry.snippet_products_slider = SnippetProductsSlider;

    return SnippetProductsSlider;
});
