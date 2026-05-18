---
name: canonical-activity-time-contract
overview: Standardize activity/subactivity schedule data to one canonical backend API contract (local date + local time + time_zone semantics) and migrate admin portal + mobile app consumers to that contract in a breaking rollout.
todos:
  - id: backend-contract-unification
    content: Unify activity/subactivity schedule response shape across all backend read endpoints and align schemas/tests.
    status: completed
  - id: admin-portal-migration
    content: Regenerate admin API types and migrate schedule parsing/display/write flows to canonical local date/time + time_zone contract.
    status: completed
  - id: mobile-app-migration
    content: Regenerate mobile API client and migrate schedule domain/display/grouping/expiration logic to canonical contract semantics.
    status: completed
  - id: cross-project-validation
    content: Run backend/admin/mobile regression checks focused on schedule rendering, editing, and date grouping behaviors.
    status: completed
isProject: false
---

# Canonical Activity Timezone Contract Rollout

## Goal
Move all activity/subactivity schedule APIs and clients to one contract:
- `start_date` / `end_date`: `YYYY-MM-DD` (local calendar date)
- `start_time` / `end_time`: `HH:mm:ss` wall time (no offset)
- `time_zone`: IANA timezone (required for activity + subactivity)
- instant fields (enrollment windows/timeslots) stay RFC3339 with explicit offset

## Backend API Standardization
- Create a shared schedule serializer and use it in all activity read routes so response shape is identical across details/list/search/bulk.
- Remove date/time formatting paths that currently output mixed shapes (`formatHkIsoWithOffset` for date-only fields, raw Date JSON, `toISOString()` where not intended).
- Ensure routes that return details-shaped payloads always include `time_zone` for activity and subactivity.
- Align TypeBox/OpenAPI schemas to canonical schedule shapes and keep instant fields explicitly typed as `date-time`.

Key files:
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getActivityDetails.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getActivityDetails.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/utils/processActivityDetails.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/utils/processActivityDetails.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getActivitiesDetails.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getActivitiesDetails.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getActivitiesByIds.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getActivitiesByIds.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/postBulkDetailsActivities.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/postBulkDetailsActivities.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/searchActivities.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/searchActivities.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/searchActivitiesByGroup.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/searchActivitiesByGroup.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getSearchPublishedActivities.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getSearchPublishedActivities.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getMeActivitiesPublishedOverview.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/routes/activities/getMeActivitiesPublishedOverview.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/utils/activityTimezone.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/utils/activityTimezone.ts)
- [/home/jacky-ng/stewards-repo/stewards-back-api/src/utils/formatHkApiDatetime.ts](/home/jacky-ng/stewards-repo/stewards-back-api/src/utils/formatHkApiDatetime.ts)

## Admin Portal Migration
- Regenerate API types after backend contract update.
- Introduce one schedule adapter utility for parse/display/submit to remove scattered string assumptions.
- Refactor activity/subactivity editors and displays to consume canonical local date/time + `time_zone` (remove `1970-01-01T` hacks and mixed parser logic).
- Update bulk XLSX parser/export assumptions to preserve local calendar date and wall time consistently.

Key files:
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/types/api.d.ts](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/types/api.d.ts)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/utils/subactivityScheduleHelpers.ts](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/utils/subactivityScheduleHelpers.ts)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/DateTimeCard.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/DateTimeCard.tsx)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/ScheduleCard.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/ScheduleCard.tsx)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/utils/getPeriod.ts](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/utils/getPeriod.ts)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/CompactActivityInfoCard.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/CompactActivityInfoCard.tsx)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/ActivityDetailsCard.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/activity/ActivityDetailsCard.tsx)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/application/PublishedActivitySearch.tsx](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/components/cards/application/PublishedActivitySearch.tsx)
- [/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/utils/activityBulkRows.ts](/home/jacky-ng/stewards-repo/stewards-front-admin-portal-vite/app/utils/activityBulkRows.ts)

## Mobile App Migration
- Regenerate OpenAPI client and adjust generated model expectations for canonical schedule fields.
- Add one domain-level schedule interpreter (civil date/time + zone) used by details, cards, calendar grouping, and expiration checks.
- Refactor places using parsed `DateTime` components as civil dates, so they use explicit `time_zone` semantics.
- Update cache hydration and synthetic details mapping paths to preserve schedule semantics.

Key files:
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/generated_api/converters.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/generated_api/converters.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/generated_api/models/activities_details.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/generated_api/models/activities_details.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/generated_api/models/activities_details_sub_activities_item.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/generated_api/models/activities_details_sub_activities_item.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/utils/details_display_extension.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/utils/details_display_extension.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/utils/datetime_range.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/utils/datetime_range.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/provider/activities_applications_calendar_provider.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/provider/activities_applications_calendar_provider.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/ui/activities_applications_today_screen.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/ui/activities_applications_today_screen.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/utils/activity_expiration_utils.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/utils/activity_expiration_utils.dart)
- [/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/services/activity_cache_service.dart](/home/jacky-ng/stewards-repo/stewards-front-mobile-user/lib/feature/activity/services/activity_cache_service.dart)

## Validation Strategy
- Backend: add/adjust contract tests to assert exact schedule string shapes per endpoint and verify consistent `time_zone` presence.
- Admin portal: regression checks for activity details, subactivity editor round-trip, published search cards, and bulk import parsing.
- Mobile app: regression checks for details display, calendar grouping by day, today list ordering, and expiration behavior under canonical schedule inputs.

## Delivery Order
1. Backend canonical contract + tests.
2. Regenerate admin/mobile API clients.
3. Admin portal adapter + component migrations.
4. Mobile schedule-domain migration.
5. Cross-client regression pass.