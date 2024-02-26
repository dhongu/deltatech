# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Object History for Service",
    "summary": "Extends Object History for Agreement an Equipment models",
    "version": "14.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Other",
    "depends": [
        "deltatech_object_history",
        "deltatech_service",
        "deltatech_service_equipment",
    ],
    "license": "OPL-1",
    "data": [
        "views/service_agreement.xml",
        "views/service_equipment.xml",
        "views/object_history.xml",
    ],
    # "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
