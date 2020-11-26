odoo.define("deltatech_no_quick_create.fields", function (require) {
    "use strict";

    var relational_fields = require("web.relational_fields");
    var FieldMany2One = relational_fields.FieldMany2One;

    FieldMany2One.include({
        init: function () {
            this._super.apply(this, arguments);
            this.nodeOptions = _.defaults(this.nodeOptions, {
                quick_create: false,
                no_quick_create: true,
            });
        },
    });
});
