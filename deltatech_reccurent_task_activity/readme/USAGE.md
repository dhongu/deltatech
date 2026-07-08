This module works automatically, with no configuration needed.

- When a recurring task's next occurrence is created in Project, the module
  automatically creates a **To Do** activity (`mail.mail_activity_data_todo`,
  which must remain available) for every user assigned to the task.
- The first occurrence of a recurring task does not get an activity; only the
  subsequent occurrences do.
- The activity is created for each occurrence, with the task name as summary
  and the task's deadline as due date, so assigned users are reminded to
  handle the new occurrence.
