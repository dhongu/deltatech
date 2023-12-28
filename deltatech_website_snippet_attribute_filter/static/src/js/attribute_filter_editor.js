odoo.define("deltatech_website_snippet_attribute_filter.attribute_filter_editor", function (require) {
    "use strict";

    var Wysiwyg = require("web_editor.wysiwyg");

    Wysiwyg.include({
        start: function () {
            const $items = $(".s_attribute_filter_item").find("select");
            $items.select2("destroy");
            return this._super(...arguments);
        },
    });

    const options = require("web_editor.snippets.options");

    options.registry.attribute_filter_editor = options.Class.extend({
        cleanForSave: function () {
            const $items = $(".s_attribute_filter_item").find("select");
            $items.select2("destroy");
        },

        async _renderCustomXML(uiFragment) {
            this.attributeLists = await this._rpc({
                model: "product.attribute",
                method: "name_search",
                args: ["", []],
                context: this.options.recordInfo.context,
            });
            if (this.attributeLists.length) {
                const selectEl = uiFragment.querySelector('we-select[data-attribute-name="attributeId"]');
                for (const attributeList of this.attributeLists) {
                    const button = document.createElement("we-button");
                    button.dataset.selectDataAttribute = attributeList[0];
                    button.textContent = attributeList[1];
                    selectEl.appendChild(button);
                }
            }
        },
    });
});
