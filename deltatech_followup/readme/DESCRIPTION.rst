
Features:
 -  Configure followup items:
      - Name - name of the followup
      - Code - can be used in cron jobs to run only selected followups
      - Active - if the followup items will be processed or not
      - Date field - invoice date or due date
      - relative days from configured date field (i.e. -5 means 5 days before, 3 means 3 days after)
      - mail subject
      - mail from
      - mail body (with pre-configured blocks - please see field help)
 - Configure Partners
      - will receive followups - check if the partner will be processed for followups
 - Configure cron job for followup mails:
      - model: Followup Send (followup.send)
      - Python code:
          - for all followups: model.run_followup()
          - for selected followups: model.run_followup(["12D", "20D"]) - 12D and 20D are the codes of the followups to run

- An override partner id can be configured for testing purposes. In system parameters, parameter name -> "followup.override_partner_id", value -> id of the partner
