Operators who work in other windows or away from the screen miss the
notifications shown in the corner of the Odoo backend. This module plays a
short sound with each backend notification, with a different sound for each
notification type, so the operator hears what happened without watching the
screen.

**A sound per notification type.** Each notification shown in the backend
plays a sound that depends on its type:

- success: `notify.wav`;
- warning (also used for notifications without a type): `exclamation.wav`;
- error: `error.wav`;
- info: `bell.wav`.

The sound files are in `static/src/sounds/` and can be replaced.

**Sound on or off per user.** The **Enable notification sounds** option,
checked by default, turns the sounds on or off for one user. The change takes
effect after the page is reloaded.

## Configuration

Nothing to configure: the sounds play as soon as the module is installed. To
turn them off for a user, open *Settings > Users & Companies > Users*, open
the user, go to the *Preferences* tab and uncheck **Enable notification
sounds**.

## Limitations

- The option is on the user form used by administrators only; users cannot
  change it themselves from *My Preferences*.
- Browsers may block sounds until the user has clicked or typed on the page,
  so the first notification after loading the page can be silent. Mobile
  browsers may mute these sounds.
