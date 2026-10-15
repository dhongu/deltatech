import {NotificationPlugin} from "@web/core/notifications/notification_plugin";
import {patch} from "@web/core/utils/patch";
import {user} from "@web/core/user";

const SOUND_MAP = {
    success: "/deltatech_notification_sound/static/src/sounds/notify.wav",
    warning: "/deltatech_notification_sound/static/src/sounds/exclamation.wav",
    danger: "/deltatech_notification_sound/static/src/sounds/error.wav",
    info: "/deltatech_notification_sound/static/src/sounds/bell.wav",
};

// The visible notification defaults to "warning" when no type is given, so we
// mirror that here to keep the audio cue consistent with what the user sees.
const DEFAULT_TYPE = "warning";

function playSound(type) {
    // Fail open: only stay silent when the user explicitly disabled the sounds.
    // `session.user_context` is consumed (and deleted) by `@web/core/user`,
    // so the preference is read from `user.context`.
    if (user.context.notification_sound_enabled === false) {
        return;
    }
    const url = SOUND_MAP[type || DEFAULT_TYPE];
    if (!url) {
        return;
    }
    try {
        const audio = new Audio(url);
        audio.preload = "auto";
        // Some browsers block autoplay until the first user interaction; ignore silently.
        Promise.resolve(audio.play()).catch(() => {
            // Autoplay blocked by the browser; nothing to do.
        });
    } catch {
        // Ignore playback errors.
    }
}

// In 20.0 the notifications are handled by `NotificationPlugin`; the legacy
// `notification` service only wraps it, while other plugins (e.g. the bus
// `simple_notification`) use the plugin directly. Patching the plugin
// covers every notification.
patch(NotificationPlugin.prototype, {
    add(message, options = {}) {
        playSound(options.type);
        return super.add(...arguments);
    },
});
