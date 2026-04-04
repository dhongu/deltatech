update queue_job set state='cancelled' where state in ('pending','enqueued','started');
