# 0001: Search filters live in the URL query string

Status: accepted, 2026-09-29. Contract: [FILTERS.md](../../FILTERS.md).

## Context

Another application needs to know which filters a shopper has applied on a search
page, and to open a search page with filters already applied. The site is static
HTML, so it has no server-side state to query.

## Assumptions

- The consumer can read the page URL, and some consumers can do nothing else. None of them can call an API on this site.
- There is one dealer and one inventory feed, so param names do not need a dealer or site namespace.
- Hosting is static. There is no server to parse routes or store sessions.
- Filtering runs in the browser over fewer than about 100 cards per page, so re-filtering on every change is cheap.
- Facet labels are stable enough to use as values. A label containing a comma is rare, but it happens (`Sun, Sound & NAV Group`).

## Decision

- Each filter is one named query param (`brand`, `category`, `priceRangeLow`, ...).
- A multi-select facet uses one param, with values joined by a literal comma. Values OR within a param and AND across params.
- Ranges are plain integers. Sort and view are params too.
- Only active filters are written. `history.replaceState` updates the URL live, and loading a URL restores the full state.
- `_build/gen.py` (`FACET_DEFS`) is the single source for param names and emits `window.FACET_MAP`, so `js/site.js` never hard-codes them.

## Consequences

- Any URL is a shareable, bookmarkable search, and a consumer that reads only URLs sees the full filter state.
- Param names become a public contract. Renaming one breaks consumers, so a rename needs a new ADR.
- Commas inside labels need special handling on read (`readUrl` in `js/site.js`).
- Filter changes do not add browser history entries, so Back leaves the page.

## Alternatives considered

- **Repeated params (`brand=Jeep&brand=RAM`).** Rejected because the URLs are longer and harder to read, and a consumer has to collect the repeats instead of splitting one value.
- **Hash state (`#brand=Jeep`).** Rejected because some URL readers drop the hash, and it is not sent to servers or analytics.
- **`pushState` per change.** Rejected because Back would step through every checkbox click.
