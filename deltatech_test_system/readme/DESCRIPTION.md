A test copy of a database is easy to mistake for production. This module marks a database as test or production, shows a banner on test ones, and hides the Apps screen's install and uninstall buttons on production ones.

- **Test or production**: The *Database Is Neutralized* setting, in the company section of the general settings, marks a test database. The text below it reads *It is a test system* or *It is a productive system*.
- **Neutralization on save**: Saving with the box newly ticked runs the `data/neutralize.sql` script of every installed module that has one. Saving again does not repeat it, and clearing the box does not undo what the scripts changed.
- **Test banner**: Each time the settings are saved, the web client's neutralization banner (`web.neutralize_banner`) is switched on or off to match the box.
- **Safer Apps screen**: On a database that is not neutralized, the module cards and form hide the install and uninstall buttons, and each card shows *Is installed* or *Is not installed*.
- **Notification bar**: When the system parameter `database_notification_banner` holds a text, internal users see it in a yellow bar. The parameter has no settings screen, and neutralizing the database deletes it.

The module depends on `web` and has no security groups of its own.
