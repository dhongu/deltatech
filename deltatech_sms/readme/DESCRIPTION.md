Send the SMS messages that Odoo generates through your own SMS provider account
instead of Odoo IAP credits. Two providers are supported: **4Pay** (sms.4pay.ro)
and **Wapi** (smswapi.com).

**Provider replaces Odoo IAP for SMS.** Every SMS queued by Odoo (from the chatter,
SMS marketing, SMS templates, automated actions) is sent one by one through the
provider set on the SMS IAP account. No IAP credits are used, and the Twilio
provider of Odoo 20, if configured, is bypassed as well.

**4Pay.** The message is sent with an HTTP GET to the 4Pay customer API, using the
service ID and the password of your 4Pay account.

**Wapi.** The message is sent with an HTTP POST to the Wapi API, through one of
the Android devices linked to your Wapi account (SIM 1).

**Text without diacritics.** Accents are removed from the message before sending
(for example "ă" becomes "a"), so the text fits the GSM character set.

**Sending status.** A message the provider accepts goes to the standard Odoo
*Pending* state and is deleted from the queue like any sent SMS. A message the
provider rejects goes to *Error* (server error) and stays in the queue, so it
can be resent; the answer of the provider is written to the server log.

## Configuration

Go to *Settings > Technical > IAP > In-App Purchase Accounts* (developer mode)
and open the account of the **SMS** service (create it if it is missing). In the
*Account Information* group of the form, fill in:

- **SMS Provider**: *SMS 4Pay* or *SMS Wapi*.
- **SMS Secret**: the 4Pay password, or the Wapi API secret.
- **SMS Gateway**: the 4Pay service ID (servID), or the Wapi device ID.

## Limitations

- The provider endpoints are fixed in the code; other gateways or custom URLs
  cannot be configured.
- Delivery reports are not received from the provider: a sent SMS stays
  *Pending* and never reaches *Delivered*.
- The SMS account registration and sender-name verification flows of Odoo IAP
  do not work while this module is installed.
