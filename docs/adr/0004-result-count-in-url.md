# 0004: Listing pages write the match count to the URL as `resultCount`

Status: accepted, 2026-09-30. Contract: [FILTERS.md](../../FILTERS.md#result-count),
[PAGE-CONTEXT.md](../../PAGE-CONTEXT.md#resultcount).

## Context

A consumer reading a listing URL (filters per [0001](0001-filter-url-query-contract.md),
context per [0002](0002-page-context-contract.md)) could see what the shopper asked
for but not how many vehicles that produced. Recomputing it would need the full
inventory. The page already knows the number: it shows it as "(N)" in the heading.

## Assumptions

- Consumers read the URL or `window.pageContext`, as for filters and compare.
- All matching cards are in the DOM, so the match count is a cheap client-side count
  and is not capped by a page size.
- A count is only meaningful where the filter sidebar runs (the three search pages,
  clearance, electric). Nobody needs it on home, VDPs or other content pages.
- Nobody needs to drive the page with a count; it is output only.

## Decision

- `resultCount=<n>`, `n` = cards matching the active filters (the heading number,
  not the page size). Always written on listing pages, including unfiltered.
- Position: after facets and ranges, before `sort`/`view`, before the compare params.
- Page-owned: in `SiteUrl.owned()`, never read as input, overwritten with the real
  count on load. Other pages strip it.
- Written on load, on every filter change and after "Clear all". The compare block
  rewrites the URL through `SiteUrl.rewrite`, which the filter engine points at its
  own `writeUrl`, so a compare change keeps `resultCount` in its slot.
- Mirrored as `window.pageContext.resultCount` (number), set before
  `pagecontext:change` fires. The generator emits the unfiltered count.

## Consequences

- A consumer gets the result size from the URL alone, and can spot an empty result.
- The URL of an unfiltered listing page is no longer just the context params.
- A shared link carries a count that may be stale by the time it is opened; the page
  corrects it on load, so it must be trusted only after `js/site.js` runs.
- One more public param name. Renaming it needs a new ADR.

## Alternatives considered

- **`pageContext` only, no URL param.** Rejected: URL-only consumers are a stated
  audience of 0001/0002.
- **Write it last, after compare.** Rejected: compare is documented as always last
  ([0003](0003-compare-selection-in-url.md)), and the count belongs with the filters
  that produce it.
- **Read it as input (e.g. a page size).** Rejected: it would mean two things, and a
  stale link would change what the page shows.
