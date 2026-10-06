# 0006: Demo `openRecalls` on VDPs

Status: accepted, 2026-10-05. Contract: [PAGE-CONTEXT.md](../../PAGE-CONTEXT.md#vehicle).
Code: `DEMO_OPEN_RECALLS` and `vehicle_context` in `_build/gen.py`, and `VEHICLE` in
`js/site.js`.

## Context

The Optimy plugin's nudges are driven by VDP URL params. Demoing an open-recall nudge
needs a VDP that says the car has an open recall. The scrape has no recall data.

## Assumptions

- This is a demo site. One car with a recall is enough to show the nudge, and nobody
  reads the value as a real recall status.
- Consumers read the value from the VDP URL or `window.pageContext.vehicle`, like the
  other vehicle params.
- The flagged car (used 2024 Jeep Compass, id 14351116) stays in the inventory.

## Decision

- `gen.py` holds a `DEMO_OPEN_RECALLS` table keyed by vehicle id, currently
  `{'14351116': 1}`. `vehicle_context` exposes it as `vehicle.openRecalls`
  (number, `null` when absent).
- The VDP URL writes `openRecalls` right after `mileage`, only when non-null. It is
  page-owned like every vehicle param: an incoming value is overwritten, or stripped
  on cars without one.
- Nothing visible on the VDP changes, and `_build/inventory.json` is not edited.

## Consequences

- `/used/2024-Jeep-Compass-id14351116.html` loads with `...&mileage=94770&openRecalls=1&...`.
- The recall is fabricated and will disagree with the real vehicle's history.
- Adding more demo recalls is a one-line change to the table and a regenerate.
- If the car leaves the inventory, the entry silently does nothing.

## Alternatives considered

- **Set it in `js/site.js` by URL path.** Rejected: the value would be missing from the
  generated `pageContext`, and data would live in two places.
- **Write it into `_build/inventory.json`.** Rejected for the same reason as ADR 0005:
  fabricated values would be mixed into the scraped source with nothing marking them.
- **Always write `openRecalls=0` on other cars.** Rejected: there is no real data, so
  `0` would claim the car has no recalls. `null`/absent says "unknown".
