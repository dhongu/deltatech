odoo.define("deltatech_website_category_snippet.category_card_editor", function (require) {
    const options = require("web_editor.snippets.options");
    const s_dynamic_snippet_carousel_options = require("website.s_dynamic_snippet_carousel_options");

    const SnippetCategorySliderOptions = s_dynamic_snippet_carousel_options.extend({
        init: function () {
            this._super.apply(this, arguments);
            this.productCategories = {};
        },

        // OnBuilt: function () {
        //     this._super.apply(this, arguments);
        //     this._rpc({
        //         route: "/website_sale/snippet/options_filters",
        //     }).then((data) => {
        //         if (data.length) {
        //             this.$target.get(0).dataset.filterId = data[0].id;
        //             this.$target.get(0).dataset.numberOfRecords = this.dynamicFilters[data[0].id].limit;
        //             this._refreshPublicWidgets();
        //             // Refresh is needed because default values are obtained after start()
        //         }
        //     });
        // },

        _computeWidgetVisibility: function (widgetName) {
            if (widgetName === "filter_opt") {
                return false;
            }
            return this._super.apply(this, arguments);
        },

        _fetchProductCategories: function () {
            return this._rpc({
                model: "product.public.category",
                method: "search_read",
                kwargs: {
                    domain: [],
                    fields: ["id", "name"],
                },
            });
        },

        _renderCustomXML: async function (uiFragment) {
            await this._super.apply(this, arguments);
            await this._renderProductCategorySelector(uiFragment);
        },

        _renderProductCategorySelector: async function (uiFragment) {
            const productCategories = await this._fetchProductCategories();
            for (const index in productCategories) {
                this.productCategories[productCategories[index].id] = productCategories[index];
            }
            const productCategoriesSelectorEl = uiFragment.querySelector('[data-name="product_category_opt"]');
            return this._renderSelectUserValueWidgetButtons(productCategoriesSelectorEl, this.productCategories);
        },

        _setOptionsDefaultValues: function () {
            this._super.apply(this, arguments);
            const templateKeys = this.$el.find(
                "we-select[data-attribute-name='templateKey'] we-selection-items we-button"
            );
            if (templateKeys.length > 0) {
                this._setOptionValue("templateKey", templateKeys.attr("data-select-data-attribute"));
            }
            const productCategories = this.$el.find(
                "we-select[data-attribute-name='productCategoryId'] we-selection-items we-button"
            );
            if (productCategories.length > 0) {
                this._setOptionValue("productCategoryId", productCategories.attr("data-select-data-attribute"));
            }
        },
    });

    options.registry.snippet_category_slider = SnippetCategorySliderOptions;
});
