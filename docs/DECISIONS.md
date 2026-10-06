# Decisions

A flat registry of decisions. Each links to its ADR in [adr/](adr/), which explains
the convention in [adr/README.md](adr/README.md).

| # | Decision | Date | Status | Contract |
|---|---|---|---|---|
| [0001](adr/0001-filter-url-query-contract.md) | Search filters live in the URL query string, with multiple values joined by commas | 2026-09-29 | Accepted | [FILTERS.md](../FILTERS.md) |
| [0002](adr/0002-page-context-contract.md) | Page type comes from the URL, with VDPs at the real site's `-id<id>.html` paths. Detail comes from `window.pageContext` and the `pagecontext:*` events | 2026-09-29 | Accepted | [PAGE-CONTEXT.md](../PAGE-CONTEXT.md) |
| [0002 amendment](adr/0002-page-context-contract.md#amendment-2026-09-29-context-also-in-the-query-string) | Every page also writes its context (`pageType`, `inventoryType`, `pageName`, VDP vehicle) to the front of the query string on load, and corrects stale values. Unfiltered search pages are no longer bare URLs | 2026-09-29 | Accepted | [PAGE-CONTEXT.md](../PAGE-CONTEXT.md#context-in-the-query-string) |
| [0003](adr/0003-compare-selection-in-url.md) | The compare selection (max 4) lives in the URL as `compare` + `compareStock`, last, written only at 2+, restored by stock | 2026-09-29 | Accepted | [FILTERS.md](../FILTERS.md#compare) |
| [0004](adr/0004-result-count-in-url.md) | Listing pages write the filtered match count as `resultCount` (after ranges, before sort/view and compare), page-owned, also in `pageContext.resultCount`; stripped elsewhere | 2026-09-30 | Accepted | [FILTERS.md](../FILTERS.md#result-count) |
| [0005](adr/0005-demo-used-price-reductions.md) | Used cars with a "Reduced Price" badge get a deterministic demo reduction (3–8% from a stock-number hash, nearest $50, min $300) added in `gen.py`, not in the source data. VDPs write `priceDrop` (= `originalPrice - price`) after `originalPrice`, page-owned | 2026-09-30 | Accepted | [PAGE-CONTEXT.md](../PAGE-CONTEXT.md#vehicle) |
| [0006](adr/0006-demo-open-recalls.md) | VDPs carry a demo `openRecalls` count from a `DEMO_OPEN_RECALLS` table in `gen.py` (only used 2024 Jeep Compass id 14351116 = 1), written after `mileage` only when set, page-owned | 2026-10-05 | Accepted | [PAGE-CONTEXT.md](../PAGE-CONTEXT.md#vehicle) |
