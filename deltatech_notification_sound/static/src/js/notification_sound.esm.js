import {notificationService} from "@web/core/notifications/notification_service";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

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
    if (session.user_context?.notification_sound_enabled === false) {
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

patch(notificationService, {
    start() {
        const service = super.start(...arguments);
        const originalAdd = service.add;
        service.add = (message, options = {}) => {
            playSound(options.type);
            return originalAdd(message, options);
        };
        return service;
    },
});
