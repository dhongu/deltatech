odoo.define("deltatech_widget_fontawesome.fontawesome_fields", function (require) {
    "use strict";
    var AbstractField = require("web.AbstractField");
    var core = require("web.core");
    var field_registry = require("web.field_registry");

    var _lt = core._lt;

    /*

     */

    var FieldFontAwesome = AbstractField.extend({
        description: _lt(""),
        supportedFieldTypes: ["selection", "many2one", "char"],

        _render: function () {
            if (this.value) {
                var className = this.value;
                this.$el.html("<i/>");
                this.$el.addClass("fa " + className);
            }
        },
    });

    field_registry.add("fontawesome", FieldFontAwesome);

    return FieldFontAwesome;
});
