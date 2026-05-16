# Notification Flow

This document describes the current notification system across the Stewards monorepo.

---

## Data Model

The core entity is `scheduled_notifications` in Prisma, which stores all notifications (immediate or scheduled).

### Key Fields

- **status**: `draft` → `pending` → `locked` → `sent` / `failed` / `partial` / `canceled`
- **notification_type**: `broadcast`, `topic`, `organization`, `activity`, `person`, `individual`, `active_activity_application`
- **notification_target**: JSON storing the target scope (e.g. `{ organization_id }`, `{ activity_id }`, `{ person_ids }`)
- **fcm_topics**: JSON array for topic-based delivery (e.g. `['all_stewards']`)
- **schedule_config** / **is_recurring** / **recurrence_pattern**: for recurring notifications
- **`data.image_file_id`** (optional): UUID of a **`core_files`** row that is **public** (`is_public`) and has MinIO `bucket`/`key`. At send time the backend resolves it to `{API_HOST}/api/public/files/{id}` and sets FCM rich-notification image fields (`notification.imageUrl`, Android `notification.imageUrl`, APNS `fcmOptions.imageUrl`). Configure **`API_HOST`** on the API and on **`scheduled-notification-cron`** / **`notification-consumer`** to the public HTTPS base URL of this API so Google’s FCM servers can download the image.

### Supporting Tables

- `person_fcm_tokens` — stores FCM device tokens per person
- `sent_notifications_memberships` — audit trail of which memberships received a notification
- `membership_fcm_topics` — links memberships to FCM topic subscriptions

---

## Backend Services (stewards-back-api)

### Service Layers

| Service | Role |
|---------|------|
| `NotificationService` | Orchestration — creates, schedules, sends notifications |
| `ScheduledNotificationService` | CRUD for `scheduled_notifications` records |
| `FcmNotificationService` | Actual FCM delivery — topic, token, multicast (batches of 500) |
| `FcmTokenService` | Resolves FCM tokens from org/activity/person IDs |

### API Routes (`src/routes/notifications/`)

| Endpoint | Purpose |
|----------|---------|
| `POST /notifications/broadcast` | Broadcast to all stewards via `all_stewards` topic |
| `POST /notifications/organization/:org_id` | Send to members of an organization |
| `POST /notifications/activity/:activity_id` | Send to activity participants |
| `POST /notifications/members` | Send to specific members |
| `POST /notifications/schedule` | Schedule with optional recurrence |
| `POST /notifications/active-activity-application` | Send to members with active applications |
| Each of the above also has a `*Draft` variant | Creates in draft status |
| `PATCH /notifications/draft` | Edit draft |
| `PATCH /notifications/draft/publish` | Promote draft to pending |
| `PATCH /notifications/pending/unpublish` | Demote pending back to draft |
| `PATCH /notifications/scheduled` | Edit scheduled notification |
| `POST /notifications/:id/retry` | Retry failed/partial notification |
| `GET /notifications` | Paginated list with filters |
| `DELETE /notifications` | Soft delete |

---

## Workers & Queues

### RabbitMQ Queues

| Queue | Producer | Consumer Worker | Purpose |
|-------|----------|-----------------|---------|
| `mobile_notifications` | `postOrganizationNotification` route | `notification-consumer` | Organization push notifications |
| `activity_update_notifications` | API routes | `notification-consumer` | Activity change notifications to applicants |
| `application_update_notifications` | API routes | `notification-consumer` | Application status change notifications |

### Cron Worker

**`scheduled-notification-cron`** — runs every minute (Asia/Hong_Kong timezone):

1. Unlocks expired locks (`locked` → `pending` when past `scheduled_at`)
2. Locks upcoming notifications (`pending` → `locked` within 15 minutes of send time)
3. Fetches due `pending` notifications where `scheduled_at <= now`
4. Resolves FCM tokens via `FcmTokenService` based on notification type/target
5. Sends via Firebase Admin (`notification` payload includes optional image URL when `data.image_file_id` is set)
6. For recurring notifications, calls `scheduleNextRecurrence()` (daily/weekly/monthly)

---

## Delivery Mechanisms

- **Topic-based**: FCM topics like `all_stewards`, `organization_<id>`, `activity_<id>`, `member_<id>` — used for broadcast and topic types
- **Token-based**: Direct FCM token delivery from `person_fcm_tokens` — used for organization, activity, person, and active_activity_application types
- **Multicast**: Batched in groups of 500 tokens (`FCM_MULTICAST_BATCH_SIZE`)

---

## Frontend Admin Portal

### Pages

- `/organizations/:org_code/notifications` — main notification management page (requires `notification:read` permission)
- Activity record pages include a `ScheduledNotificationsCard` for activity-specific notifications

### User Flows

1. **Create**: Dialogs on the notifications page — `CreateOrganizationNotificationDialog`, `CreateActivityNotificationDialog`, or from an activity record via `CreateActivityNotificationSimpleDialog`
2. **Draft workflow**: Create as draft → Edit → Publish (draft → pending)
3. **Manage**: Edit, publish, unpublish (pending → draft), delete, retry failed
4. **View**: Paginated table with status/type/search filters, status and topic badges

### Status Lifecycle

```
Draft  →  Publish  →  Pending  →  [cron locks within 15min]  →  Locked  →  Sent / Failed / Partial
  ↑                      |
  └── Unpublish ─────────┘
```

---

## End-to-End Flow

1. **Admin creates** a notification via the admin portal (immediate or scheduled, draft or direct)
2. **API route** validates and calls `NotificationService` / `ScheduledNotificationService` to persist a `scheduled_notifications` record
3. **If immediate**: the route calls `FcmNotificationService` directly to send via Firebase
4. **If scheduled**: the record sits as `pending` until `scheduled-notification-cron` picks it up at the scheduled time
5. **Cron worker** (every minute) locks, resolves recipients' FCM tokens, sends via Firebase, updates status to `sent`/`failed`/`partial`, and schedules next recurrence if applicable
6. **For organization notifications specifically**: the route also publishes to the `mobile_notifications` RabbitMQ queue, consumed by `notification-consumer`
7. **For activity/application updates**: separate queues (`activity_update_notifications`, `application_update_notifications`) handle system-triggered notifications
