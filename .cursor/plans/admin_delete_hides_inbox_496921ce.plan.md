---
name: admin delete hides inbox
overview: Enable admins to delete sent notifications from the admin portal and ensure the deletion path used by the portal reliably hides those notifications from the mobile inbox APIs.
todos:
  - id: allow-delete-sent-ui
    content: Allow delete action for sent notifications in admin portal table actions while preserving permission checks.
    status: pending
  - id: align-delete-copy
    content: Update delete confirmation/i18n text to reflect that deleted notifications no longer appear in mobile inbox.
    status: pending
  - id: harden-delete-route
    content: Make delete handler behavior explicit for already-deleted/nonexistent notifications to avoid confusing admin UX.
    status: pending
  - id: verify-api-flow
    content: "Verify delete flow against getMeSentNotifications: item present before delete and absent after delete."
    status: pending
  - id: add-regression-tests
    content: Add targeted backend regression test for inbox exclusion after scheduled notification soft delete.
    status: pending
isProject: false
---

# Make Admin Deletion Hide Mobile Inbox Items

## What I found
- Admin portal currently only shows the Delete action for `pending`/`draft` rows in [stewards-front-admin-portal-vite/app/routes/notifications/index.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/routes/notifications/index.tsx), so staff cannot delete already-sent notifications.
- The backend delete endpoint `DELETE /api/notifications/:notification_id` in [stewards-back-api/src/routes/notifications/deleteScheduledNotification.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/notifications/deleteScheduledNotification.ts) soft-deletes `scheduled_notifications`.
- Mobile inbox list (`GET /api/me/members/:order_number/notifications/sent`) in [stewards-back-api/src/routes/notifications/getMeSentNotifications.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/notifications/getMeSentNotifications.ts) already filters out rows where linked `scheduled_notifications.deleted_at` is not null.

## Plan
- Update admin portal row-action gating so `sent` notifications can also be deleted (while keeping permission checks), in [stewards-front-admin-portal-vite/app/routes/notifications/index.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/routes/notifications/index.tsx).
- Review/delete UX copy and confirmation messaging to ensure it clearly states the effect (deletion hides from member inbox), using existing i18n keys in [stewards-front-admin-portal-vite/public/locales/zh-HK/notifications.json](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/public/locales/zh-HK/notifications.json) and EN counterpart.
- Add a backend guard/clarity check so deleting an already-deleted notification is handled predictably (idempotent response or explicit not-found handling) in [stewards-back-api/src/services/ScheduledNotificationService.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/services/ScheduledNotificationService.ts) and route handler if needed.
- Validate end-to-end behavior manually:
  - create/send notification
  - confirm it appears in mobile inbox API (`getMeSentNotifications`)
  - delete in admin
  - confirm it disappears from inbox API results
- Add/adjust focused backend test coverage around inbox exclusion after deletion (target route tests for `getMeSentNotifications`), and (if present) admin portal behavior checks for delete action availability on sent rows.

## Scope notes
- No data hard-delete is required; existing soft-delete + inbox query filters are sufficient.
- No change to mobile app client contract is required if backend filtering remains the same.