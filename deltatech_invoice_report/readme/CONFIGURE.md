## Cron job

After installation a scheduled action named **Update Product Invoice History by
Year** is created under **Settings > Technical > Automation > Scheduled
Actions**. It is active by default and runs every day.

- To change the frequency, open the scheduled action and adjust **Interval** and
  **Interval Unit**.
- To disable automatic refresh, set the action to inactive; users can still
  refresh individual products manually via the **Refresh** button on the
  History tab.

## Initial population of the history table

The cron job populates the history table on its first run. If you want the data
available immediately after installation, trigger the cron manually:

1. Go to **Settings > Technical > Automation > Scheduled Actions**.
2. Open **Update Product Invoice History by Year**.
3. Click **Run Manually**.
