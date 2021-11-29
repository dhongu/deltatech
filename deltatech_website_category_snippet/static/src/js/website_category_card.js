odoo.define("deltatech_website_category_snippet.category_card", function (require) {
    "use strict";

    const publicWidget = require("web.public.widget");
    const DynamicSnippetCarousel = require("website.s_dynamic_snippet_carousel");

    const SnippetCategorySlider = DynamicSnippetCarousel.extend({
        selector: ".s_snippet_category_slider",

        _isConfigComplete: function () {
            return this._super.apply(this, arguments) && this.$el.get(0).dataset.productCategoryId !== undefined;
        },

        _mustMessageWarningBeHidden: function () {
            const isInitialDrop = this.$el.get(0).dataset.templateKey === undefined;
            return isInitialDrop || this._super.apply(this, arguments);
        },

        _getSearchDomain: function () {
            const searchDomain = this._super.apply(this, arguments);
            const productCategoryId = parseInt(this.$el.get(0).dataset.productCategoryId);
            if (productCategoryId >= 0) {
                searchDomain.push(["public_categ_ids", "child_of", productCategoryId]);
            }
            return searchDomain;
        },
    });
    publicWidget.registry.snippet_category_slider = SnippetCategorySlider;

    return SnippetCategorySlider;
});
