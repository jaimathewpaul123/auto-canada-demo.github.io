# 0003: The compare selection lives in the URL, keyed by stock

Status: accepted, 2026-09-29. Contract: [FILTERS.md](../../FILTERS.md#compare),
[PAGE-CONTEXT.md](../../PAGE-CONTEXT.md#compare).

## Context

Shoppers can tick up to four vehicle cards to compare. Another application needs to
read which cars are ticked, and to open a page with them already ticked, the same way
it reads filters ([0001](0001-filter-url-query-contract.md)) and page context
([0002](0002-page-context-contract.md)). There is no compare page yet, only the selection.

## Assumptions

- Consumers read the URL or `window.pageContext`, as for filters and context. Nothing else is available.
- Stock numbers are unique across all inventory and contain no commas. Compare names are not unique (eleven `2026 Jeep Compass North` in new inventory).
- Comparing makes sense only with 2 or more cars. A consumer gains nothing from a single tick.
- Four is enough to compare and still fits one comparison screen. Nobody needs more.
- A selection only needs to survive on the page it was made on. Each card page restores only the stocks it shows.

## Decision

- Two params, `compare` (display names) and `compareStock` (stock numbers), in tick order, encoded like the facets: a literal comma between values, each value `encodeURIComponent`-ed on its own.
- Written only while 2 or more are ticked, via `history.replaceState`, and always last: after the context, filter, range, sort and view params. `SiteUrl.replace` appends them through a `tail` hook, so the filter engine and the compare block never drop each other's params.
- Maximum 4. At 4, the other checkboxes are disabled with a tooltip.
- On load, only `compareStock` is read. Unknown stocks are dropped, and the page rewrites both params from its own cards, so `compare` is page-owned like the context params.
- Selection is independent of filters. "Clear all" keeps it, and hidden cards stay ticked.
- `window.pageContext.compare` mirrors the URL (`[]` below 2), and a change fires `pagecontext:change`.

## Consequences

- A compare URL is shareable, and a consumer gets names without a lookup.
- Two new public param names. Renaming either needs a new ADR.
- Ticking one car changes neither the URL nor `pageContext`, so no event fires until the second tick.
- A selection does not carry across pages. A used-car stock in the URL of the new search page is dropped.

## Alternatives considered

- **Names only.** Rejected: names collide, so a restore by name would tick the wrong car.
- **Stock only.** Rejected: consumers would need an inventory lookup to show anything, and the brief wants readable names.
- **Always write the params, even at 0 or 1.** Rejected: URLs for the common no-compare case get noisier, and one car is not a comparison.
- **`localStorage`.** Rejected: invisible to URL-only consumers and not shareable.
- **Trust `compare` on load.** Rejected: it is display text, and an edited or stale name would be reported as truth.
