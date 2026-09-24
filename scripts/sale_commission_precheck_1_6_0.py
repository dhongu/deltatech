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
        SELECT user_id, journal_id, company_id, ARRAY_AGG(id ORDER BY id)
          FROM commission_users WHERE journal_id IS NOT NULL
      GROUP BY user_id, journal_id, company_id HAVING COUNT(*) > 1
        """
    )
    for user_id, journal_id, _company_id, ids in dups:
        user = env["res.users"].sudo().browse(user_id)
        journal = env["account.journal"].sudo().browse(journal_id)
        verdict(
            "DE FĂCUT",
            f"dublură {ids}: {user.name} pe {journal.display_name}. Liniile raportului sunt acum dublate; "
            "păstrați un singur rând (unicitatea nu se aplică până atunci)",
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
    sale_rel = table_exists("sale_order_line_invoice_rel")
    no_order = (
        q(
            """
        SELECT COUNT(DISTINCT m.id), COUNT(l.id), COALESCE(SUM(l.quantity * l.purchase_price), 0)
          FROM account_move m
          JOIN account_move_line l ON l.move_id = m.id AND l.display_type = 'product' AND l.product_id IS NOT NULL
         WHERE m.move_type = 'out_refund' AND m.state = 'posted'
           AND m.invoice_date >= now() - interval '1 month' * %(months)s
           AND NOT EXISTS (SELECT 1 FROM sale_order_line_invoice_rel r WHERE r.invoice_line_id = l.id)
        """,
            {"months": MONTHS},
        )
        if sale_rel
        else [(0, 0, 0)]
    )
    value_only = (
        q(
            """
        SELECT COUNT(DISTINCT m.id), COUNT(l.id), COALESCE(SUM(l.quantity * l.purchase_price), 0)
          FROM account_move m
          JOIN account_move_line l ON l.move_id = m.id AND l.display_type = 'product' AND l.product_id IS NOT NULL
         WHERE m.move_type = 'out_refund' AND m.state = 'posted' AND COALESCE(l.purchase_price, 0) <> 0
           AND m.invoice_date >= now() - interval '1 month' * %(months)s
           AND EXISTS (SELECT 1 FROM sale_order_line_invoice_rel r WHERE r.invoice_line_id = l.id)
           AND NOT EXISTS (
                SELECT 1 FROM sale_order_line_invoice_rel r
                  JOIN stock_move sm ON sm.sale_line_id = r.order_line_id AND sm.state = 'done'
                  JOIN stock_location dl ON dl.id = sm.location_dest_id AND dl.usage = 'internal'
                  JOIN stock_location sl ON sl.id = sm.location_id AND sl.usage = 'customer'
                 WHERE r.invoice_line_id = l.id)
        """,
            {"months": MONTHS},
        )
        if sale_rel
        else [(0, 0, 0)]
    )
    moves, lines, cost = no_order[0]
    print(f"  Fără comandă de vânzare: {moves} note, {lines} linii, cost pe linii {cost:,.2f}")
    if moves:
        verdict(
            "ATENȚIE",
            "notele de credit noi fără comandă vor avea cost 0. Dacă firma face astfel retururi de marfă "
            "(storno manual), profitul lor scade cu toată valoarea: costul trebuie pus manual",
        )
    moves, lines, cost = value_only[0]
    print(f"  Cu comandă, fără retur în stoc, cu cost > 0: {moves} note, {lines} linii, cost {cost:,.2f}")
    if moves:
        verdict(
            "ATENȚIE",
            "notele existente nu se schimbă la actualizare. Se trec pe cost 0 doar dacă se rulează "
            "Actualizare preț achiziție pe ele (inclusiv cu „Pentru toate liniile”): profitul și "
            "comisionul calculat scad cu acest cost",
        )
    if not (no_order[0][0] or value_only[0][0]):
        verdict("OK", "nicio notă de credit afectată")

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
