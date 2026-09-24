"""Verificare înainte de actualizarea deltatech_sale_commission la 19.0.1.6.0.

Doar citește: rulează numai SELECT-uri și face rollback la final, deci se poate rula pe baza
productivă. Arată ce se schimbă la client după actualizare, ca să se decidă înainte:

    odoo-bin shell -c <config> -d <baza> --no-http < scripts/sale_commission_precheck_1_6_0.py

Pe odoo.sh, din shell-ul instanței:

    odoo-bin shell --no-http < sale_commission_precheck_1_6_0.py

Fiecare secțiune se încheie cu OK, ATENȚIE (se schimbă ceva ce trebuie aprobat) sau DE FĂCUT
(trebuie curățat înainte sau imediat după actualizare).
"""

# ruff: noqa: F821  (`env` e dat de odoo-bin shell)
# pylint: disable=print-used

MODULE = "deltatech_sale_commission"
MONTHS = 12  # istoricul analizat pentru notele de credit și plăți


def q(sql, params=None):
    env.cr.execute(sql, params or ())
    return env.cr.fetchall()


def table_exists(name):
    return bool(q("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (name,)))


def section(title):
    print("\n" + "=" * 78 + "\n" + title + "\n" + "-" * 78)


def verdict(level, text):
    print(f"  -> {level}: {text}")


def users_of(xmlid):
    group = env.ref(xmlid, raise_if_not_found=False)
    if not group:
        return env["res.users"]
    return group.sudo().with_context(active_test=True).all_user_ids.filtered(lambda u: u.active and not u.share)


def names(users, limit=15):
    shown = ", ".join(f"{u.name} ({u.login})" for u in users[:limit])
    return shown + (f" … și încă {len(users) - limit}" if len(users) > limit else "")


def run():
    module = env["ir.module.module"].sudo().search([("name", "=", MODULE)])
    section("0. Modul")
    if not module or module.state != "installed":
        verdict("OK", f"{MODULE} nu e instalat; nu e nimic de verificat")
        return
    print(f"  Versiune instalată: {module.latest_version}")
    dependents = (
        env["ir.module.module.dependency"]
        .sudo()
        .search([("name", "=", MODULE), ("module_id.state", "=", "installed")])
        .module_id
    )
    if dependents:
        print("  Module instalate care depind de el: " + ", ".join(sorted(dependents.mapped("name"))))
        verdict("ATENȚIE", "verificați suprascrierile din aceste module (get_purchase_price, write pe raport)")
    else:
        verdict("OK", "niciun alt modul instalat nu depinde de el")

    # ------------------------------------------------------------------ parametri
    section("1. Parametrul days_for_commission")
    value = env["ir.config_parameter"].sudo().get_param(f"{MODULE}.days_for_commission")
    print(f"  Valoare: {value!r}")
    if value is False or not str(value).strip():
        verdict("OK", "lipsește sau e gol: comisionul nu depinde de încasare, ca înainte")
    elif str(value).strip() == "0":
        verdict(
            "DE FĂCUT",
            "0 însemna „fără condiție”; după actualizare înseamnă „încasată cel târziu la scadență”. "
            "Dacă se dorește fără condiție, goliți parametrul înainte de actualizare",
        )
    else:
        try:
            days = int(value)
        except ValueError:
            verdict("DE FĂCUT", "valoare nenumerică: până acum crăpa calculul, după actualizare e refuzată cu mesaj")
        else:
            if days < 0:
                verdict("DE FĂCUT", "valoare negativă: după actualizare e refuzată la calcul")
            else:
                verdict("OK", f"{days} zile, comportament neschimbat")
    detail = env["ir.config_parameter"].sudo().get_param("sale_commission.sale_user_detail", "invoice")
    print(f"  Comision agent de vânzări (sale_user_detail): {detail}")

    # ------------------------------------------------------------------ drepturi
    section("2. Drepturi")
    managers = users_of(f"{MODULE}.group_commission_manager")
    viewers = users_of(f"{MODULE}.group_commission_viewer") - managers
    print(f"  Administrator comisioane ({len(managers)}): {names(managers) or '-'}")
    print(f"  Doar Vizualizare comisioane ({len(viewers)}): {names(viewers) or '-'}")
    if viewers:
        verdict(
            "ATENȚIE",
            "acești utilizatori nu vor mai putea marca plata, modifica rânduri sau rula asistenții. "
            "Dacă lucrează efectiv cu comisioanele, dați-le Administrator comisioane",
        )
    # cine a marcat plăți sau a modificat comisioane în ultimele luni (ultima scriere pe linie)
    rows = q(
        """
        SELECT l.write_uid, COUNT(*)
          FROM account_move_line l
         WHERE (l.commission_paid OR COALESCE(l.commission, 0) <> 0)
           AND l.write_date >= now() - interval '1 month' * %(months)s
      GROUP BY l.write_uid
        """,
        {"months": MONTHS},
    )
    writers = env["res.users"].sudo().browse([uid for uid, _count in rows if uid]).exists()
    outside = writers.filtered(lambda u: u not in managers and u.id != 1 and not u.has_group("base.group_system"))
    if outside:
        verdict(
            "DE FĂCUT",
            "au modificat linii cu comision fără a fi Administrator comisioane (vor primi eroare de acces): "
            + names(outside),
        )
    elif not managers:
        verdict("DE FĂCUT", "nimeni nu are Administrator comisioane: nimeni nu va mai putea calcula comisioanele")
    else:
        verdict("OK", "cei care au lucrat cu comisioanele sunt Administrator comisioane")

    # ------------------------------------------------------------------ commission.users
    section("3. Comisioane agenți (commission.users)")
    total = q("SELECT COUNT(*) FROM commission_users")[0][0]
    print(f"  Rânduri: {total}")
    # aceeași regulă ca pre-migrarea 19.0.1.6.0
    filled = q(
        """
        WITH single_journal AS (
            SELECT company_id, MIN(id) AS journal_id FROM account_journal
             WHERE type = 'sale' GROUP BY company_id HAVING COUNT(*) = 1
        )
        SELECT DISTINCT ON (cu.user_id, cu.company_id) cu.id, cu.user_id, sj.journal_id
          FROM commission_users cu
          JOIN single_journal sj ON sj.company_id = cu.company_id
         WHERE cu.journal_id IS NULL
           AND NOT EXISTS (SELECT 1 FROM commission_users o WHERE o.user_id = cu.user_id
                            AND o.company_id = cu.company_id AND o.journal_id = sj.journal_id)
      ORDER BY cu.user_id, cu.company_id, cu.id
        """
    )
    no_journal = q("SELECT id, user_id, company_id FROM commission_users WHERE journal_id IS NULL ORDER BY id")
    left = [row for row in no_journal if row[0] not in {f[0] for f in filled}]
    if filled:
        users = env["res.users"].sudo().browse([f[1] for f in filled])
        verdict(
            "ATENȚIE",
            f"migrarea completează jurnalul pe rândurile {[f[0] for f in filled]} ({names(users)}). "
            "Până acum nu se potriveau cu nicio factură; după actualizare agenții primesc comision "
            "calculat și pe facturile din trecut",
        )
    if left:
        verdict(
            "DE FĂCUT",
            f"rândurile {[r[0] for r in left]} rămân fără jurnal (firma are mai multe jurnale de vânzări "
            "sau agentul are deja rândul pe jurnal): completați jurnalul sau ștergeți-le",
        )
    dups = q(
        """
        SELECT user_id, journal_id, company_id, ARRAY_AGG(id ORDER BY id),
               COUNT(DISTINCT (rate, manager_rate, director_rate, manager_user_id, director_user_id))
          FROM commission_users WHERE journal_id IS NOT NULL
      GROUP BY user_id, journal_id, company_id HAVING COUNT(*) > 1
        """
    )
    for user_id, journal_id, _company_id, ids, variants in dups:
        user = env["res.users"].sudo().browse(user_id)
        journal = env["account.journal"].sudo().browse(journal_id)
        impact = (
            "ACUM raportul are vânzarea, costul, profitul și comisionul calculat înmulțite cu "
            f"{len(ids)} pe facturile acestui agent din acest jurnal; verificați comisioanele deja plătite"
        )
        if variants == 1:
            verdict(
                "ATENȚIE",
                f"dublură identică {ids}: {user.name} pe {journal.display_name}. {impact}. "
                f"Migrarea păstrează rândul {ids[0]} și le șterge pe celelalte",
            )
        else:
            verdict(
                "DE FĂCUT",
                f"dublură cu rate diferite {ids}: {user.name} pe {journal.display_name}. {impact}. "
                "După actualizare raportul folosește rândul cel mai vechi; păstrați un singur rând, cu "
                "rata corectă (unicitatea în baza de date se aplică abia după curățare)",
            )
    wrong_type = q(
        """
        SELECT cu.id FROM commission_users cu JOIN account_journal j ON j.id = cu.journal_id
         WHERE j.type <> 'sale' ORDER BY cu.id
        """
    )
    if wrong_type:
        verdict("ATENȚIE", f"rândurile {[r[0] for r in wrong_type]} au un jurnal care nu e de vânzări")
    if not (filled or left or dups or wrong_type):
        verdict("OK", "toate rândurile au jurnal de vânzări și nu există dubluri")

    # ------------------------------------------------------------------ note de credit
    section(f"4. Note de credit (ultimele {MONTHS} luni)")
    # aceeași clasificare ca get_purchase_price după actualizare
    rows = q(
        """
        WITH lines AS (
            SELECT l.id, m.id AS move_id, COALESCE(l.quantity * l.purchase_price, 0) AS cost,
                   EXISTS (
                       SELECT 1 FROM sale_order_line_invoice_rel r
                         JOIN stock_move sm ON sm.sale_line_id = r.order_line_id AND sm.state = 'done'
                         JOIN stock_location sl ON sl.id = sm.location_id AND sl.usage = 'customer'
                         JOIN stock_location dl ON dl.id = sm.location_dest_id AND dl.usage IN ('internal', 'supplier')
                        WHERE r.invoice_line_id = l.id) AS has_return,
                   EXISTS (
                       SELECT 1 FROM sale_order_line_invoice_rel r
                         JOIN sale_order_line sol ON sol.id = r.order_line_id AND sol.is_downpayment
                        WHERE r.invoice_line_id = l.id) AS is_downpayment,
                   EXISTS (
                       SELECT 1 FROM account_move_line o
                        WHERE o.move_id = m.reversed_entry_id AND o.display_type = 'product'
                          AND o.product_id = l.product_id AND o.product_uom_id = l.product_uom_id
                          AND ROUND(o.price_unit::numeric, 4) = ROUND(l.price_unit::numeric, 4)
                          AND ROUND(COALESCE(o.discount, 0)::numeric, 2) = ROUND(COALESCE(l.discount, 0)::numeric, 2)
                   ) AS is_reversal
              FROM account_move m
              JOIN account_move_line l ON l.move_id = m.id AND l.display_type = 'product' AND l.product_id IS NOT NULL
             WHERE m.move_type = 'out_refund' AND m.state = 'posted'
               AND m.invoice_date >= now() - interval '1 month' * %(months)s
        )
        SELECT CASE WHEN has_return THEN 'retur'
                    WHEN is_downpayment THEN 'avans'
                    WHEN is_reversal THEN 'storno'
                    ELSE 'reducere' END AS kind,
               COUNT(DISTINCT move_id), COUNT(*), COALESCE(SUM(cost), 0),
               COUNT(*) FILTER (WHERE cost <> 0), COALESCE(SUM(cost) FILTER (WHERE cost <> 0), 0)
          FROM lines GROUP BY 1
        """,
        {"months": MONTHS},
    )
    by_kind = {row[0]: row[1:] for row in rows}
    labels = {
        "retur": "Cu retur de marfă (cost din retur, neschimbat)",
        "avans": "Pe avans (neschimbat)",
        "storno": "Stornare a facturii, același preț (preia costul facturii, neschimbat)",
        "reducere": "Reducere de preț sau notă fără factură, fără retur (cost 0)",
    }
    for kind, label in labels.items():
        moves, lines, cost, _with_cost, _cost_with = by_kind.get(kind, (0, 0, 0, 0, 0))
        print(f"  {label}: {moves} note, {lines} linii, cost {cost:,.2f}")
    _moves, _lines, _cost, with_cost, cost_with = by_kind.get("reducere", (0, 0, 0, 0, 0))
    if with_cost:
        verdict(
            "ATENȚIE",
            f"{with_cost} linii de reducere au azi cost ({cost_with:,.2f}), deci profit supraevaluat. "
            "Actualizarea nu le schimbă; le trece pe cost 0 doar Actualizare preț achiziție rulat pe ele "
            "(inclusiv cu „Pentru toate liniile”). Notele de reducere noi primesc direct cost 0",
        )
    else:
        verdict("OK", "nicio notă de credit de reducere cu cost")
    if by_kind.get("reducere", (0,))[0]:
        verdict(
            "ATENȚIE",
            "o notă fără factură stornată și fără retur legat de comandă (storno manual al unei mărfi "
            "returnate fizic) primește și ea cost 0: costul se pune manual",
        )

    # ------------------------------------------------------------------ în plată
    section("5. Facturi „În plată”")
    rows = q(
        """
        SELECT COUNT(DISTINCT m.id), COUNT(l.id)
          FROM account_move m
          JOIN account_move_line l ON l.move_id = m.id AND l.display_type IN ('product', 'discount')
         WHERE m.move_type IN ('out_invoice', 'out_receipt') AND m.state = 'posted'
           AND m.payment_state = 'in_payment' AND COALESCE(l.commission, 0) = 0
           AND m.invoice_date >= now() - interval '1 month' * %(months)s
        """,
        {"months": MONTHS},
    )
    moves, lines = rows[0]
    print(f"  Facturi în plată, cu linii fără comision: {moves} facturi, {lines} linii")
    if moves:
        verdict(
            "ATENȚIE",
            "la următorul calcul aceste linii primesc comision (erau tratate ca neîncasate). "
            "Apar și în filtrul „Plătit” și în asistentul deschis fără selecție",
        )
    else:
        verdict("OK", "nicio factură în plată fără comision")

    # ------------------------------------------------------------------ cost 0
    section(f"6. Linii facturate cu cost 0 (ultimele {MONTHS} luni)")
    rows = q(
        """
        SELECT COUNT(l.id)
          FROM account_move m
          JOIN account_move_line l ON l.move_id = m.id AND l.display_type = 'product' AND l.product_id IS NOT NULL
         WHERE m.move_type IN ('out_invoice', 'out_receipt') AND m.state = 'posted'
           AND COALESCE(l.purchase_price, 0) = 0
           AND m.invoice_date >= now() - interval '1 month' * %(months)s
        """,
        {"months": MONTHS},
    )
    print(f"  Linii: {rows[0][0]}")
    if rows[0][0]:
        verdict(
            "ATENȚIE",
            "„Marchează plătit” nu le mai pune tacit costul produsului: profitul rămâne supraevaluat "
            "până la Actualizare preț achiziție",
        )
    else:
        verdict("OK", "nicio linie cu cost 0")

    # ------------------------------------------------------------------ model eliminat
    section("7. Modelul eliminat sale.commission.condition")
    if table_exists("sale_commission_condition"):
        count = q("SELECT COUNT(*) FROM sale_commission_condition")[0][0]
        if count:
            verdict(
                "DE FĂCUT", f"{count} rânduri se pierd la actualizare (tabela e ștearsă); exportați-le dacă contează"
            )
        else:
            verdict("OK", "tabela e goală")
    else:
        verdict("OK", "tabela nu există")


try:
    run()
finally:
    env.cr.rollback()
    print("\nGata. Scriptul nu a modificat nimic (rollback).")
