# 0002: Page type from the URL, detail from `window.pageContext`

Status: accepted, 2026-09-29. Amended 2026-09-29 (see [Amendment](#amendment-2026-09-29-context-also-in-the-query-string)). Contract: [PAGE-CONTEXT.md](../../PAGE-CONTEXT.md).
Builds on [0001](0001-filter-url-query-contract.md).

## Context

An external application needs to know which kind of page it is on (home, a search
page, a vehicle detail page, a content page), and on a VDP it needs the vehicle's
details. VDPs used to live at `vehicle/<id>.html`. That path did not match the
real site and did not say which inventory the vehicle came from.

## Assumptions

- Some consumers can only read the URL. Others can run script on the page, such as a widget or an injected tag.
- There is one dealer on static hosting. Paths are fixed at build time, and there is no server to add headers or endpoints.
- The real site's VDP paths (`/new/inventory/…-id<id>.html`, `/used/…`, `/demos/…`) are stable, and each inventory record carries its path in `url`.
- The vehicle data is small (about 20 fields) and changes only when the site is rebuilt.

## Decision

- Two layers, each with its own job:
  - **The URL gives the page type.** VDPs are generated at each record's `url`, mirroring the real site, so `/(new/inventory|used|demos)/…-id<digits>.html` identifies a VDP and its inventory type.
  - **`window.pageContext` gives the detail.** The generator emits it inline in `<head>` (mirrored as `<body data-page-type data-inventory-type>`). It holds `pageType`, `inventoryType`, a typed `vehicle` on VDPs, and `filters` on search pages.
- `js/site.js` fires `pagecontext:ready` once the filters have been read from the URL, and `pagecontext:change` whenever they change.
- `filters` uses the 0001 param names, so the page and the URL share one vocabulary.

## Consequences

- A consumer that reads only URLs can detect every page type and get the vehicle id. A script consumer gets typed data without scraping the page.
- VDP paths are now a public contract. Moving them needs a new ADR, and links to the old `vehicle/<id>.html` paths no longer work.
- The object is built at build time, so it can only be as current as the last rebuild. That is acceptable because the page is too.
- Search pages and VDPs share the `used/` and `demos/` directories, so detection must match the whole filename pattern, not the directory alone.

## Alternatives considered

- **URL-only (vehicle fields as query params on the VDP link).** Rejected because it duplicates data the page already has, makes URLs long, and every link that forgot the params would be wrong.
- **JS object only, keeping opaque `vehicle/<id>.html` URLs.** Rejected because consumers that read only URLs could not detect a VDP or its inventory type.

## Amendment 2026-09-29: context also in the query string

### Context

The consuming application decides what to show from the URL alone. It does not run
script on the page and does not match paths against the VDP pattern. Under the
original decision it could not read the page type, inventory type, content page
name or vehicle without implementing the path rules, and it could not see the
vehicle at all.

### Assumptions

- The consumer reads the URL of the page as it is after load (from the address bar
  or a navigation event), not the link that was clicked. A link as typed is not
  corrected until the page runs `js/site.js`.
- `history.replaceState` with a changed query string works on every host the site
  is opened from, including `file://` in Chrome, as the filters already rely on.
- The vehicle fields are few enough (19 params) that the VDP URL stays usable.
- There is no server-side routing, so the query string has no other meaning on
  these pages and the page is free to rewrite it.

### Decision

- On load, every page rewrites its URL with `history.replaceState` so the query
  string leads with `pageType`, then `inventoryType`, then `pageName`, then on VDPs
  the vehicle params, then any filter, `sort` and `view` params. The order and names
  are in [PAGE-CONTEXT.md](../../PAGE-CONTEXT.md#context-in-the-query-string).
- VDP vehicle params use the [0001](0001-filter-url-query-contract.md) filter names
  where a field is also a filter (`brand` for make, `category` for body style), so
  a VDP URL reads like a filter set pinned to one car. `imageUrl`, `url` and
  `badge` are left out.
- The page owns its context params. Incoming values are ignored as input and
  overwritten, so a stale or edited URL is corrected. On search pages `year`,
  `model` and the rest remain filters.
- The path rules and `window.pageContext` stay as they are. The query string is
  written from `window.pageContext`, so the three cannot disagree after load.

### Consequences

- A URL-only consumer gets every page's context, and the full vehicle on VDPs, with
  one `URLSearchParams` call.
- An unfiltered search page is no longer a bare URL, and "Clear all" keeps the
  context params. [FILTERS.md](../../FILTERS.md) is updated to match.
- VDP URLs are long. Sharing one pastes the vehicle data too, which the page then
  overwrites with current values on load.
- The query string on VDPs now carries the vehicle, which the original decision
  rejected as input. It is still not input: the page writes it and never reads it.

### Alternatives considered

- **Keep path-only detection.** Rejected because the consumer reads only the URL
  and would have to reimplement the path rules and still could not get the vehicle.
- **Write only `pageType` and `vehicleId`.** Rejected because the consumer would
  still need a lookup to get the vehicle, and it has no API to call.
- **Put the context in `#hash`.** Rejected for the same reason as in 0001: some URL
  readers drop the hash.
- **Trust incoming context params.** Rejected because a stale or hand-edited link
  would make the URL disagree with the page.
