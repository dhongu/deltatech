# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CommissionUsers(models.Model):
    _name = "commission.users"
    _description = "Users commission"

    user_id = fields.Many2one("res.users", string="Salesperson", required=True)
    name = fields.Char(string="Name", related="user_id.name")
    rate = fields.Float(string="Rate", default=0.01, digits=(12, 3))
    manager_rate = fields.Float(string="Rate manager", default=0, digits=(12, 3))
    manager_user_id = fields.Many2one("res.users", string="Sales Manager")
    director_rate = fields.Float(string="Rate director", default=0, digits=(12, 3))
    director_user_id = fields.Many2one("res.users", string="Sales Director")
    # The margin report joins the rates on salesperson *and* journal: a row without a journal
    # never matches an invoice, and two rows on the same pair duplicate the report lines.
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        domain="[('type', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    _user_journal_company_unique = models.Constraint(
        "UNIQUE(user_id, journal_id, company_id)",
        "A salesperson can have only one commission rate per journal and company.",
    )

    @api.constrains("user_id", "journal_id", "company_id")
    def _check_unique_user_journal(self):
        # Same rule as the SQL constraint, checked by the ORM: it still applies on a database where
        # the unique index could not be created because of duplicates left from an older version.
        for record in self:
            # sudo: the duplicate to find may belong to a company the current user does not have
            # active, and a record rule would hide it. The check would then pass and leave in place
            # the very duplicate the margin report can not cope with.
            if self.sudo().search_count(
                [
                    ("id", "!=", record.id),
                    ("user_id", "=", record.user_id.id),
                    ("journal_id", "=", record.journal_id.id),
                    ("company_id", "=", record.company_id.id),
                ]
            ):
                raise ValidationError(
                    self.env._(
                        "%(user)s already has a commission rate on the journal %(journal)s.",
                        user=record.user_id.display_name,
                        journal=record.journal_id.display_name,
                    )
                )

    @api.constrains("journal_id", "company_id")
    def _check_journal_company(self):
        """The row must belong to the company of its journal.

        The margin report matches the rates on salesperson, journal *and* company, so a row whose
        company is not the one of its journal matches no invoice at all: the salesperson quietly
        gets no commission, with nothing on screen to say why. The domain on journal_id already
        prevents it in the form, but a domain is not enforced on the server — an import or an
        ``env[...].create()`` goes straight past it.
        """
        for record in self:
            journal_company = record.journal_id.company_id
            if journal_company and journal_company != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The journal %(journal)s belongs to %(journal_company)s, but the commission "
                        "rate is set on %(company)s. The margin report would ignore this rate.",
                        journal=record.journal_id.display_name,
                        journal_company=journal_company.display_name,
                        company=record.company_id.display_name,
                    )
                )
