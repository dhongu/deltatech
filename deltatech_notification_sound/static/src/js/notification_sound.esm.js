import {onMounted, onWillUpdateProps} from "@odoo/owl";
import {Notification} from "@web/core/notifications/notification";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";

const SOUND_MAP = {
    success: "/deltatech_notification_sound/static/src/sounds/notify.wav",
    warning: "/deltatech_notification_sound/static/src/sounds/exclamation.wav",
    danger: "/deltatech_notification_sound/static/src/sounds/error.wav",
    info: "/deltatech_notification_sound/static/src/sounds/bell.wav",
};

let ENABLED_CACHE = true;
let ENABLED_PROMISE = false;

async function fetchEnabledOnce() {
    if (ENABLED_CACHE !== undefined) {
        return ENABLED_CACHE;
    }
    if (ENABLED_PROMISE) {
        return ENABLED_PROMISE;
    }
    // Use Odoo's RPC service to get session info once and cache the flag
    ENABLED_PROMISE = (async () => {
        try {
            const result = await rpc("/web/session/get_session_info");
            const enabledFromServer = result.user_context.notification_sound_enabled;
            ENABLED_CACHE = enabledFromServer;
        } catch {
            // Fail open: if we can't determine, default to true to preserve previous behavior
            ENABLED_CACHE = true;
        }
        return ENABLED_CACHE;
    })();
    return ENABLED_PROMISE;
}

async function playSound(url) {
    try {
        const audio = new Audio(url);
        audio.preload = "auto";
        // Some browsers block autoplay; ignore errors silently
        await audio.play();
    } catch {
        // Ignore errors
    }
}

async function maybePlay(props) {
    if (!props || !props.type) return;
    const url = SOUND_MAP[props.type];
    if (!url) return;
    const enabled = await fetchEnabledOnce();
    if (!enabled) return;
    await playSound(url);
}

patch(Notification.prototype, {
    setup() {
        // Call original setup first (if any), then register hooks
        if (this._super) {
            this._super(...arguments);
        }

        onMounted(() => {
            // Fire and forget; hooks don't await
            maybePlay(this.props);
        });
        onWillUpdateProps((nextProps) => {
            maybePlay(nextProps);
        });
    },
});
