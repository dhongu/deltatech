Overview:
Adds audible feedback to Odoo backend notifications so operators are alerted instantly without watching the screen.

Features:
- Plays different sounds depending on notification type:
  - Success → notify.wav
  - Warning → exclamation.wav
  - Error (danger) → error.wav
  - Info → bell.wav
- Seamless integration with the backend (no extra UI); patches the OWL component `web.NotificationWowl`.
- Assets are loaded via `web.assets_backend` (JS + XML + sounds).
- Per‑user toggle in Preferences: each user can enable/disable notification sounds from their profile.

How it works (technical):
- Frontend logic is handled in JS (`static/src/js/notification_sound.js`) by patching the Notification OWL component and using OWL hooks (`onMounted`, `onWillUpdateProps`) to play a sound when a notification appears/updates.
- The module reads the user preference via the Odoo RPC service:
  - `const result = await rpc("/web/session/get_session_info");`
  - The module caches the boolean `result.user_context.notification_sound_enabled` so only one RPC is performed per page load.
- Backend exposes the preference through:
  - new field `res.users.notification_sound_enabled` (default True)
  - `ir.http.session_info()` enriched to include the flag in `user_context`.
- Sound files live under `static/src/sounds/` and can be replaced if desired.

Installation & Usage:
1) Install the module like any other addon.
2) Use Odoo normally; when a backend notification pops (success/warning/error/info), a short sound plays automatically.
3) To disable sounds for your account, open Settings → Users → Your user → Preferences and uncheck "Enable notification sounds". Reload the page to refresh the session preference.

Compatibility:
- Odoo 18 (web backend).
- Modern desktop browsers. Note: Browser auto‑play policies may require at least one prior user interaction with the page before sounds can play.

Troubleshooting / Notes:
- If your browser blocks auto‑play, the first notification may be silent until you interact (click/keypress) on the page.
- After changing the preference, reload the page so the cached value and session info are refreshed.
- Mobile browsers may mute auto‑played audio by default.

Credits:
- Author: Terrabit, Dorin Hongu
- Maintainer: dhongu
- License: LGPL‑3
- Website: https://www.terrabit.ro
