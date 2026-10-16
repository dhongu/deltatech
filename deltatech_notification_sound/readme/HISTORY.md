## 19.0.2.0.3 (2026-10-16)

- Fixed: disabling the notification sounds in the user preferences had no effect. The preference
  was read from `session.user_context`, which `@web/core/user` deletes; it is now read from
  `user.context`. Tests check the flag in the session info (on by default, off when disabled).

## 19.0.2.0.2 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.2.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
