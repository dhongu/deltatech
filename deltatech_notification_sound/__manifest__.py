# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Notification Sound",
    "summary": "Play a different sound for success, warning, error and info notifications",
    "version": "19.0.2.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Tools",
    "depends": ["base", "web"],
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "deltatech_notification_sound/static/src/js/**/*",
        ],
    },
    "data": [
        "views/res_users_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
