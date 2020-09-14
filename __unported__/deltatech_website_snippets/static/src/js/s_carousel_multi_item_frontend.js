odoo.define("deltatech_website_snippets.s_carousel_multi_item_frontend", function(require) {
    "use strict";

    var sAnimation = require("website.content.snippets.animation");

    sAnimation.registry.js_carousel_multi_item = sAnimation.Class.extend({
        selector: ".js_carousel_multi_item",

        start: function() {
            var self = this;
            this._super.apply(this, arguments);

            self.$target.on("slide.bs.carousel", function(e) {
                /*
                    CC 2.0 License Iatek LLC 2018 - Attribution required
                */
                var $e = $(e.relatedTarget);
                var idx = $e.index();
                var itemsPerSlide = 5;
                var totalItems = $(".carousel-item").length;

                if (idx >= totalItems - (itemsPerSlide - 1)) {
                    var it = itemsPerSlide - (totalItems - idx);
                    for (var i = 0; i < it; i++) {
                        // Append slides to end
                        if (e.direction === "left") {
                            $(".carousel-item")
                                .eq(i)
                                .appendTo(".carousel-inner");
                        } else {
                            $(".carousel-item")
                                .eq(0)
                                .appendTo(".carousel-inner");
                        }
                    }
                }
            });
        },
    });
});
