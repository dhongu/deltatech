odoo.define("deltatech_website_product_slider_snippet.product_slider_editor", function (require) {
    "use strict";

    const options = require("web_editor.snippets.options");
    const s_dynamic_snippet_carousel_options = require("website.s_dynamic_snippet_carousel_options");

    const SnippetProductsSliderOptions = s_dynamic_snippet_carousel_options.extend({
        init: function () {
            this._super.apply(this, arguments);
            this.modelNameFilter = "product.product";
            const productTemplateId = $("input.product_template_id");
            this.hasProductTemplateId = productTemplateId.val();
            if (!this.hasProductTemplateId) {
                this.contextualFilterDomain.push(["product_cross_selling", "=", false]);
            }
            this.productLists = {};
        },

        onBuilt: function () {
            this._super.apply(this, arguments);
            this._rpc({
                route: "/website/snippet/options_filters",
            }).then((data) => {
                if (data.length) {
                    this.$target.get(0).dataset.filterId = data[0].id;
                    this.$target.get(0).dataset.numberOfRecords = this.dynamicFilters[data[0].id].limit;
                    this._refreshPublicWidgets();
                    // Refresh is needed because default values are obtained after start()
                }
            });
        },

        _computeWidgetVisibility: function (widgetName) {
            if (widgetName === "filter_opt") {
                return false;
            }
            return this._super.apply(this, arguments);
        },

        _fetchProductLists: function () {
            return this._rpc({
                model: "product.list",
                method: "search_read",
                kwargs: {
                    domain: [],
                    fields: ["id", "name"],
                },
            });
        },

        _renderCustomXML: async function (uiFragment) {
            await this._super.apply(this, arguments);
            await this._renderProductListSelector(uiFragment);
        },

        _renderProductListSelector: async function (uiFragment) {
            const productLists = await this._fetchProductLists();
            for (const index in productLists) {
                this.productLists[productLists[index].id] = productLists[index];
            }
            const productListSelectorEl = uiFragment.querySelector('[data-name="product_list_opt"]');
            return this._renderSelectUserValueWidgetButtons(productListSelectorEl, this.productLists);
        },

        _setOptionsDefaultValues: function () {
            this._super.apply(this, arguments);
            const templateKeys = this.$el.find(
                "we-select[data-attribute-name='templateKey'] we-selection-items we-button"
            );
            if (templateKeys.length > 0) {
                this._setOptionValue("templateKey", templateKeys.attr("data-select-data-attribute"));
            }
            const productLists = this.$el.find(
                "we-select[data-attribute-name='productListId'] we-selection-items we-button"
            );
            if (productLists.length > 0) {
                this._setOptionValue("productListId", productLists.attr("data-select-data-attribute"));
            }
        },
    });

    options.registry.snippet_products_slider = SnippetProductsSliderOptions;
});
