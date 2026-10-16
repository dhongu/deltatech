# Deltatech Cron Monitor Webhook

Acest modul oferă o soluție completă pentru monitorizarea job-urilor cron din Odoo 18.

## Caracteristici

- **Monitorizare în timp real**: Statusul execuțiilor (Success, Failed, Running).
- **Istoric Detaliat**: Log-uri complete pentru fiecare execuție, inclusiv durata și traceback-ul în caz de eroare.
- **Webhook Integration**: Trigger-ul job-urilor cron din surse externe (ex: cron-job.org).
- **Securitate**: Autentificare bazată pe semnătură HMAC-SHA256.
- **Alerte Automate**: Notificări prin email în caz de eșecuri consecutive.
- **Statistici**: Media duratei, număr total de execuții, succese și erori.

## Configurare

1. Instalați modulul în Odoo 18.
2. Navigați la **Settings > Technical > Automation > Settings** pentru a activa monitorizarea globală.
3. Pentru fiecare job cron, puteți configura opțiunile specifice în tab-ul **Monitoring** și **Webhook Configuration**.

## Webhook Endpoint

URL-ul de trigger este de forma: `https://your-odoo-domain.com/cron/webhook/<webhook_code>`

Dacă activarea semnăturii este necesară, trimiteți header-ul `X-Signature`.

## Licență

LGPL-3.0
