# Confirmed bugs — 2026-10-03

## SALEACTSEARCH-001 — P2: multi-record activity write fails on scalar read

MailActivity.write calls super then reads self.res_model and self.res_id directly. These scalar fields require a singleton; native mail.activity.write supports batches. Updating deadline/user/type on two activities therefore raises Expected singleton and rolls back, including batches unrelated to sales. Iterate/group affected records, rather than reading scalar fields on the whole set.

Evidence: complete addon, native batch write (:311–353) and scalar field __get__/ensure_one contract read. Source-only, database bulk update not executed.

## SALEACTSEARCH-002 — P2: moving activity leaves old order's stored list stale

write calculates active_activity_types only on the post-write res_id/model. Move an activity from sale A to sale B via res_id: B updates, but A retains the removed activity type in its stored Char. Moving from sale to another model likewise skips old A completely. Capture affected old and new sale orders and recompute both after write.

Evidence: native writable res_id/res_model_id fields and addon post-write-only handling traced. Requires authorized document/record reassignment; no database reassignment test executed.

## Limits

No view entry is supplied; field remains available for external customization/domain use. Type renaming and translated names stored in a global Char may need refresh/localization policy. Existing activities are not backfilled by this source; upgrade behavior not asserted without data. No database/permission/UI tests executed.
