# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Generic Partner",
    "version": "19.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Generic partner for anonymous customers, with accounting restrictions",
    "category": "Generic Modules",
    "depends": ["account", "sale"],
    "license": "OPL-1",
    "data": [
        "security/res_groups.xml",
        "data/data.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/account_journal_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
