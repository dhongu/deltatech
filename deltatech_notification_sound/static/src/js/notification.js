odoo.define("deltatech_notification_sound.Notification", function (require) {
    "use strict";


    // Var Notification = require("web.Notification");
    const AbstractWebClient = require("web.AbstractWebClient");

    // Notification.include({
    //     init: function () {
    //         this._super.apply(this, arguments);
    //         this.play_sound(this.type);
    //     },
    //
    //     play_sound: function (sound) {
    //         var src = "";
    //         if (sound === "danger") {
    //             src = "/deltatech_notification_sound/static/src/sounds/error.wav";
    //         } else if (sound === "warning") {
    //             src = "/deltatech_notification_sound/static/src/sounds/exclamation.wav";
    //         } else if (sound === "success") {
    //             src = "/deltatech_notification_sound/static/src/sounds/bell.wav";
    //         } else if (sound !== "default") {
    //             src = "/deltatech_notification_sound/static/src/sounds/notify.wav";
    //         }
    //         $("body").append('<audio src="' + src + '" autoplay="true"></audio>');
    //     },
    // });

    AbstractWebClient.include({
        _onDisplayWarning: function (e) {
            var data = e.data;
            this.play_sound(data.type);
            this._super.apply(this, arguments);
        },

        play_sound: function (sound) {
            var src = "";
            if (sound === "danger") {
                src = "/deltatech_notification_sound/static/src/sounds/error.wav";
            } else if (sound === "warning") {
                src = "/deltatech_notification_sound/static/src/sounds/exclamation.wav";
            } else if (sound === "success") {
                src = "/deltatech_notification_sound/static/src/sounds/bell.wav";
            } else if (sound !== "default") {
                src = "/deltatech_notification_sound/static/src/sounds/notify.wav";
            }
            $("body").append('<audio src="' + src + '" autoplay="true"></audio>');
        },
    });
});
