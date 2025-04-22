/** @odoo-module */

import Wysiwyg from "web_editor.wysiwyg";
import options from "web_editor.snippets.options";

Wysiwyg.include({
    start() {
        const $items = $(".s_attribute_filter_item").find("select");
        $items.select2("destroy");
        return this._super(...arguments);
    },
});

class AttributeFilterEditor extends options.Class {
    cleanForSave() {
        const $items = $(".s_attribute_filter_item").find("select");
        $items.select2("destroy");
    }

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
    }
}

options.registry.attribute_filter_editor = AttributeFilterEditor;
export default AttributeFilterEditor;
