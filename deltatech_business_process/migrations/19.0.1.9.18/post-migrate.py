# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""BUSINESS-013: Open Issues created before the business.open.issue sequence existed get a code."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    open_issues = env["business.open.issue"].with_context(active_test=False).search([("code", "in", (False, ""))])
    for open_issue in open_issues.sorted("id"):
        open_issue.code = env["ir.sequence"].next_by_code("business.open.issue")
