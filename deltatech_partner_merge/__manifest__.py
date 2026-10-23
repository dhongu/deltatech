{
    "name": "Partner Merge in Bulk",
    "summary": "Find probably duplicated partners, and merge those on the same VAT number in bulk, in minutes",
    "version": "19.0.1.2.0",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Tools",
    "depends": ["base", "deltatech_partner_match"],
    "data": [
        "security/partner_merge_security.xml",
        "security/ir.model.access.csv",
        "views/partner_merge_views.xml",
        "views/partner_duplicate_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "installable": True,
}
