# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import _, api, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

# Grupuri de persoane duplicate după email
DUPLICATE_CONTACTS_SQL = SQL(
    """
    SELECT email, array_agg(id ORDER BY id) AS partner_ids
    FROM res_partner
    WHERE email IS NOT NULL AND email != ''
      AND is_company = FALSE
      AND vat IS NULL
    GROUP BY email
    HAVING count(*) > 1
    """
)

# Grupuri de companii duplicate după CUI
DUPLICATE_COMPANIES_SQL = SQL(
    """
    SELECT vat, array_agg(id ORDER BY id) AS partner_ids
    FROM res_partner
    WHERE vat IS NOT NULL
      AND vat not in  ('','0','-')
      AND active = TRUE
      AND is_company = TRUE
      AND parent_id IS NULL
    GROUP BY vat
    HAVING count(*) > 1
    """
)

# Companii cu sufix SRL/SA/PFA/II care nu e încă în forma normalizată (S.R.L., S.A., P.F.A., I.I.).
# Fără excluderea formei normalizate, regex-urile se potrivesc și pe „S.R.L.”, iar cron-ul
# ar actualiza la nesfârșit aceleași companii.
COMPANIES_TO_NORMALIZE_SQL = SQL(
    r"""
    is_company = true
    AND (
        name ~* '.*\s+srl\s*$' OR
        name ~* '.*\s+s\.?\s*r\.?\s*l\.?\s*$' OR
        name ~* '.*\s+sa\s*$' OR
        name ~* '.*\s+s\.?\s*a\.?\s*$' OR
        name ~* '.*\s+pfa\s*$' OR
        name ~* '.*\s+ii\s*$'
    )
    AND name !~ ' (S\.R\.L\.|S\.A\.|P\.F\.A\.|I\.I\.)$'
    """
)


class ResPartnerMergeCron(models.Model):
    _inherit = "res.partner"

    def _compute_vies_valid(self):
        if self.env.context.get("skip_vies_check"):
            return
        return super()._compute_vies_valid()

    def _get_duplicate_groups(self, query: SQL, limit: int) -> list:
        self.env.cr.execute(SQL("%s ORDER BY 1 LIMIT %s", query, limit))
        return self.env.cr.fetchall()

    def _count_duplicate_groups(self, query: SQL) -> int:
        self.env.cr.execute(SQL("SELECT count(*) FROM (%s) AS duplicates", query))
        return self.env.cr.fetchone()[0]

    def _cron_merge_duplicate_contacts(self, limit=10):
        MergeWizard = self.env["base.partner.merge.automatic.wizard"]
        done = 0
        for email, ids in self._get_duplicate_groups(DUPLICATE_CONTACTS_SQL, limit):
            partners = self.env["res.partner"].browse(ids).exists()
            if len(partners) <= 1:
                continue
            main = partners[0]  # îl păstrăm ca principal
            secundar = partners[1]
            main_name, secundar_name = main.display_name, secundar.display_name
            try:
                # un merge eșuat nu anulează restul lotului
                with self.env.cr.savepoint():
                    partners.write({"parent_id": False})
                    wizard = MergeWizard.create(
                        {
                            "partner_ids": [(6, 0, [main.id, secundar.id])],
                        }
                    )
                    wizard.action_merge()
            except Exception:
                _logger.exception("Contactele cu email-ul %s nu au putut fi unite", email)
                continue
            _logger.info("Contactul %s a fost unit cu %s (Email: %s)", main_name, secundar_name, email)
            done += 1

        remaining = self._count_duplicate_groups(DUPLICATE_CONTACTS_SQL) if done else 0
        cron = self.env.ref("deltatech_actions.ir_cron_merge_contacts", raise_if_not_found=False)
        (cron or self.env["ir.cron"])._cron_report_progress(done, remaining)

    def _cron_merge_duplicate_companies(self, limit=10):
        MergeWizard = self.env["base.partner.merge.automatic.wizard"].with_context(skip_vies_check=True)
        done = 0
        for vat, ids in self._get_duplicate_groups(DUPLICATE_COMPANIES_SQL, limit):
            partners = self.env["res.partner"].browse(ids).exists()
            if len(partners) <= 1:
                continue
            partners = partners.with_context(skip_vies_check=True)
            main = partners[0]  # păstrăm prima companie ca principală
            secundar = partners[1]
            main_name, secundar_name = main.display_name, secundar.display_name
            try:
                # un merge eșuat nu anulează restul lotului
                with self.env.cr.savepoint():
                    wizard = MergeWizard.create(
                        {
                            "partner_ids": [(6, 0, [main.id, secundar.id])],
                        }
                    )
                    wizard.action_merge()
            except Exception:
                _logger.exception("Companiile cu CUI-ul %s nu au putut fi unite", vat)
                continue
            _logger.info("Compania %s a fost unită cu %s (CUI: %s)", secundar_name, main_name, vat)
            done += 1

        remaining = self._count_duplicate_groups(DUPLICATE_COMPANIES_SQL) if done else 0
        cron = self.env.ref("deltatech_actions.ir_cron_merge_companies", raise_if_not_found=False)
        (cron or self.env["ir.cron"])._cron_report_progress(done, remaining)

    def _count_companies_to_normalize(self) -> int:
        self.env.cr.execute(SQL("SELECT COUNT(*) FROM res_partner WHERE %s", COMPANIES_TO_NORMALIZE_SQL))
        return self.env.cr.fetchone()[0]

    def batch_normalize_company_names(self, batch_size=1000):
        """Normalizează numele unui lot de companii; returnează numărul de companii actualizate"""

        # noqa: W1401
        query_update = SQL(
            r"""
           UPDATE res_partner
           SET name = CASE
                          WHEN name ~* '.*\s+srl\s*$' THEN REGEXP_REPLACE(name, '\s+srl\s*$', ' S.R.L.', 'i')
                          WHEN name ~* '.*\s+s\.?\s*r\.?\s*l\.?\s*$' THEN REGEXP_REPLACE(name, '\s+s\.?\s*r\.?\s*l\.?\s*$', ' S.R.L.', 'i')
                          WHEN name ~* '.*\s+sa\s*$' THEN REGEXP_REPLACE(name, '\s+sa\s*$', ' S.A.', 'i')
                          WHEN name ~* '.*\s+s\.?\s*a\.?\s*$' THEN REGEXP_REPLACE(name, '\s+s\.?\s*a\.?\s*$', ' S.A.', 'i')
                          WHEN name ~* '.*\s+pfa\s*$' THEN REGEXP_REPLACE(name, '\s+pfa\s*$', ' P.F.A.', 'i')
                          WHEN name ~* '.*\s+ii\s*$' THEN REGEXP_REPLACE(name, '\s+ii\s*$', ' I.I.', 'i')
                          ELSE name
               END
           WHERE id IN (SELECT id
                        FROM res_partner
                        WHERE %s
                        ORDER BY id
                        LIMIT %s)
           RETURNING id
            """,
            COMPANIES_TO_NORMALIZE_SQL,
            batch_size,
        )

        self.env.flush_all()
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(query_update)
                partner_ids = [row[0] for row in self.env.cr.fetchall()]
        except Exception as e:
            _logger.error("Eroare la normalizarea numelor de companii: %s", e)
            return 0

        partners = self.browse(partner_ids)
        if partners:
            # numele a fost modificat prin SQL: recalculează câmpurile dependente (complete_name etc.)
            partners.invalidate_recordset(["name"])
            partners.modified(["name"])
        _logger.info("Normalizate %s nume de companii în acest lot", len(partners))
        return len(partners)

    @api.model
    def cron_normalize_company_names(self, batch_size=500):
        """Cron job pentru normalizarea periodică a numelor de companii"""
        _logger.info("Începe normalizarea automată a numelor de companii")

        try:
            updated_count = self.batch_normalize_company_names(batch_size=batch_size)
            remaining = self._count_companies_to_normalize() if updated_count else 0
        except Exception as e:
            _logger.error("Eroare în cron job pentru normalizarea companiilor: %s", e)
            self._notify_admins(
                _("Eroare în normalizarea companiilor: %s", e),
                _("EROARE - Normalizare companii - Cron Job"),
            )
            return

        cron = self.env.ref("deltatech_actions.cron_normalize_company_names", raise_if_not_found=False)
        (cron or self.env["ir.cron"])._cron_report_progress(updated_count, remaining)

        if not updated_count:
            _logger.info("Cron job: Nu au fost găsite companii care să necesite normalizare")
        elif not remaining:
            # notificarea către administratori doar la finalul normalizării, nu la fiecare lot
            message = _(
                "Cron job: normalizarea numelor de companii s-a încheiat (ultimul lot: %s companii)", updated_count
            )
            _logger.info(message)
            self._notify_admins(message, _("Normalizare companii - Cron Job"))

    def _notify_admins(self, body, subject):
        admin_users = self.env["res.users"].search([("groups_id", "in", self.env.ref("base.group_system").id)])
        for admin in admin_users:
            admin.partner_id.message_post(body=body, subject=subject)
