# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Object History",
    "summary": "Object history - a parallel history of Odoo documents, separated from standard Odoo messages",
    "version": "18.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Other",
    "depends": [
        "contacts",
    ],
    "license": "OPL-1",
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/object_history.xml",
        "wizard/add_history_wizard.xml",
        "views/res_partner.xml",
    ],
    # "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
