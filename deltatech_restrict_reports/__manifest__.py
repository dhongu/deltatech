# Copyright (C) 2026 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Deltatech - Restrict Reports Access",
    "summary": "Restrict Sales Analysis and Invoice Analysis reports by group: "
    "own records, all records, or no access.",
    "version": "18.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "AGPL-3",
    "category": "Tools",
    "development_status": "Beta",
    "maintainers": ["danila12"],
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "security/reports_security_groups.xml",
        "security/reports_security_rules.xml",
        "security/reports_security_actions.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
}
