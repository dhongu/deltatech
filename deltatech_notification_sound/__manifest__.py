# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Notification Sound",
    "summary": "Notification Sound",
    "version": "19.0.1.0.2",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Tools",
    "depends": ["base", "web"],
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "deltatech_notification_sound/static/src/js/**/*",
            "deltatech_notification_sound/static/src/xml/**/*",
        ],
    },
    "data": [
        "views/res_users_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
