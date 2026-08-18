{
    "name": "Partner Merge in Bulk",
    "summary": "Merge partners duplicated on the same VAT number, in bulk, in minutes instead of hours",
    "version": "19.0.1.0.0",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/partner_merge_security.xml",
        "security/ir.model.access.csv",
        "views/partner_merge_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "installable": True,
}
