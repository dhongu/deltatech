odoo.define("deltatech_website_snippet_attribute_filter.attribute_filter", function (require) {
    "use strict";

    const publicWidget = require("web.public.widget");

    var AttributeFilterItem = publicWidget.Widget.extend({
        selector: ".s_attribute_filter_item",
        events: {"change select": "_onChange"},
        start: function () {
            var def = this._super.apply(this, arguments);

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
                    .guardedCatch(always),
            ]);
        },

        _onChange: function () {
            var self = this;
            var $select = this.$el.find("select");
            var attributeId = this.$el.data("attribute-id");
            var attributeValueId = $select.find("option:selected").data("selectDataAttribute");
            this.$el.data("attribute-value-id", attributeValueId);
            this.$el.attr("data-attribute-value-id", attributeValueId);
            // Cauta toate elementele care au s_attribute_filter_item
            var $items = $(".s_attribute_filter_item");
            var attributeValueIds = [];
            var position = 0;
            for (const item of $items) {
                var $item = $(item);
                if ($item.data("attribute-id") === attributeId) {
                    break;
                }
                position++;
            }
            var link = "/shop?";
            // Pentru fiecare element adauga in data-attribute-value-ids id-urile selectate
            $items.each(function (index, element) {
                var $item = $(element);
                var attributeId = $item.data("attribute-id");
                $item.data("attribute-value-ids", attributeValueIds);
                $item.attr("data-attribute-value-ids", attributeValueIds);
                var attributeValueId = $(element).data("attribute-value-id");
                if (attributeValueId > 0) {
                    attributeValueIds.push(attributeValueId);
                    link += "&attrib=" + attributeId + "-" + attributeValueId;
                }
                if (index > position) {
                    self._readDataFromOdoo($item);
                }
                // Sa pun href cu linkul in item
                $item.find(".s_attribute_filter_result").find("a").attr("href", link);
            });
        },

        _readDataFromOdoo: function ($item) {
            var attributeId = $item.data("attribute-id");
            var attributeValueIds = $item.data("attribute-value-ids");
            const always = this._updateView.bind($item);
            this._rpc({
                route: "/shop/get_attribute_values",
                params: {
                    attribute_id: attributeId,
                    attribute_value_ids: attributeValueIds,
                },
            })
                .then(always)
                .guardedCatch(always);
        },

        _updateView(data) {
            // Scrie in log data
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
        },
    });

    publicWidget.registry.attribute_filter_item = AttributeFilterItem;
    return AttributeFilterItem;
});
