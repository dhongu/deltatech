(function () {
    'use strict';

    var website = openerp.website;
    var _t = openerp._t;

    website.snippet.options.product = website.snippet.Option.extend({
        on_prompt: function () {
            var self = this;
            return website.prompt({
                id: "editor_product_select_button",
                window_title: _t("Select a product"),
                input: _t("Product List"),
                //init: function (field) {
                //    return website.session.model('product.template')
                //            .call('name_search', ['', []], { context: website.get_context() });
                //},
            }).then(function (product_id) {
                self.$target.attr("data-id", product_id);
            });
        },
        drop_and_build_snippet: function() {
            var self = this;
            this._super();
            this.on_prompt().fail(function () {
                self.editor.on_remove();
            });
        },
        start : function () {
            var self = this;
            this.$el.find(".js_product_select").on("click", _.bind(this.on_prompt, this));
            this._super();
        },
        clean_for_save: function () {
            this.$target.addClass("hidden");
        },
    });
})();


