# Mobile: enrollment mode visibility migration

## Summary

`enrollment_modes[].visibility` changed from a **single string** enum (`public` | `private` | `members_only`) to a **JSON array of strings** whose values are:

- `activity_highlights` — surface: **activity highlights / published overview**  
  `GET /api/me/members/:order_number/activities/published/overview`
- `activity_search` — surface: **published activity search** (admin and member)  
  e.g. `GET /api/activities/published/search`,  
  `GET /api/me/members/:order_number/activities/published/search`,  
  `GET /api/activities/membership/search`

An **empty array** `[]` means the period is hidden from both highlights and search (staff can still manage applications in the admin portal).

### Data migration (existing rows)

| Old value       | New value                                      |
|-----------------|------------------------------------------------|
| `public`        | `["activity_highlights", "activity_search"]` |
| `members_only`  | `["activity_search"]`                        |
| `private`       | `[]`                                           |

## API contract

### Request (create / update enrollment mode)

Send `visibility` as an array, for example:

```json
{
  "visibility": ["activity_highlights", "activity_search"]
}
```

Omitting `visibility` on **create** defaults to both surfaces on the server.

### Response

```json
{
  "enrollment_modes": [
    {
      "visibility": ["activity_highlights", "activity_search"]
    }
  ]
}
```

## Client migration notes

1. **Types**: model `visibility` as `string[]`, not `string`.
2. **UI / badges**: map each known value to a label; join multiple with a comma or separate chips.
3. **Legacy strings**: if any cached payload still has a string, you can map:  
   `public` → both; `members_only` → `["activity_search"]`; `private` → `[]`.
4. **Past applicants**: for **published** activities, visibility does not restrict access for members who already have a relevant application history; that rule is enforced **server-side** — the mobile app does not need extra logic for it.

## Breaking change

This is a **breaking change** for any client that assumes `visibility` is a single enum string. Release mobile updates together with the backend, or coordinate a short compatibility window if needed.
