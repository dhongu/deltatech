/** @odoo-module */

import publicWidget from "web.public.widget";

class AttributeFilterItem extends publicWidget.Widget {
    constructor() {
        super(...arguments);
        this.selector = ".s_attribute_filter_item";
        this.events = {
            "change select": this._onChange.bind(this),
        };
    }

    async start() {
        const def = await super.start();

        if (this.editableMode) {
            return def;
        }
        const always = this._updateView.bind(this.$el);
        return Promise.all([
            def,
            this._rpc({
                route: "/shop/get_attribute_values",
                params: {
                    attribute_id: this.$target.data("attribute-id"),
                },
            })
                .then(always)
                .catch(always),
        ]);
    }

    _onChange() {
        const $select = this.$el.find("select");
        const attributeId = this.$el.data("attribute-id");
        const attributeValueId = $select.find("option:selected").data("selectDataAttribute");
        this.$el.data("attribute-value-id", attributeValueId);
        this.$el.attr("data-attribute-value-id", attributeValueId);

        const $items = $(".s_attribute_filter_item");
        const attributeValueIds = [];
        let position = 0;
        for (const item of $items) {
            const $item = $(item);
            if ($item.data("attribute-id") === attributeId) {
                break;
            }
            position++;
        }
        let link = "/shop?";
        $items.each((index, element) => {
            const $item = $(element);
            const itemAttributeId = $item.data("attribute-id");
            $item.data("attribute-value-ids", attributeValueIds);
            $item.attr("data-attribute-value-ids", attributeValueIds);
            const itemAttributeValueId = $(element).data("attribute-value-id");
            if (itemAttributeValueId > 0) {
                attributeValueIds.push(itemAttributeValueId);
                link += `&attrib=${itemAttributeId}-${itemAttributeValueId}`;
            }
            if (index > position) {
                this._readDataFromOdoo($item);
            }
            $item.find(".s_attribute_filter_result").find("a").attr("href", link);
        });
    }

    _readDataFromOdoo($item) {
        const attributeId = $item.data("attribute-id");
        const attributeValueIds = $item.data("attribute-value-ids");
        const always = this._updateView.bind($item);
        this._rpc({
            route: "/shop/get_attribute_values",
            params: {
                attribute_id: attributeId,
                attribute_value_ids: attributeValueIds,
            },
        })
            .then(always)
            .catch(always);
    }

    _updateView(data) {
        console.log(data);
        if (!data) {
            return;
        }

        this.attributeValues = data;
        const $select = this.find("select");
        $select.select2("destroy");
        $select.empty();
        let option = document.createElement("option");
        option.dataset.selectDataAttribute = 0;
        option.textContent = "All";
        $select.append(option);

        for (const attributeValue of this.attributeValues) {
            option = document.createElement("option");
            option.dataset.selectDataAttribute = attributeValue.id;
            option.textContent = attributeValue.name;
            $select.append(option);
        }
        $select.select2();
    }
}

publicWidget.registry.attribute_filter_item = AttributeFilterItem;
export default AttributeFilterItem;
