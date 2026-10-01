# 0005: Demo price reductions for used cars, and `priceDrop` on VDPs

Status: accepted, 2026-09-30. Contract: [PAGE-CONTEXT.md](../../PAGE-CONTEXT.md#vehicle).
Code: the "demo price reductions for used cars" block in `_build/gen.py`,
`vehicle_context` in `_build/gen.py`, and `VEHICLE` in `js/site.js`.

## Context

All 36 used listings carry a "Reduced Price" badge, but the scrape gave them no
previous price or breakdown. Their VDPs showed no reduction,
`pageContext.vehicle.originalPrice` was `null`, and so the Optimy plugin's price-drop
nudge could never fire on a used car. New cars already had a scraped breakdown
(`Retail Price` / `Employee Discount`) that drives the was-price and `originalPrice`.
Consumers also had to compute the drop themselves from two params.

## Assumptions

- This is a demo site. A plausible reduction matters more than a true one, and nobody
  relies on these numbers as real prices.
- The selling price (`price`) must stay as scraped. The inventory export and any
  price filter use it.
- Values must be stable across rebuilds, so screenshots, tests and links stay valid.
- The plugin and other consumers read `originalPrice`/`priceDrop` from
  `window.pageContext` or the VDP URL, as for the other vehicle params.

## Decision

- In `gen.py`'s data tidy, every used car with a "Reduced Price" badge, a price, and
  no `was` or `breakdown` gets
  `breakdown = [['Previous Price', price + drop], ['Price Reduction', -drop]]`,
  formatted like the new cars' strings. `pct` is 3–8 %, from
  `3 + md5(stock) % 6`. `drop = round(price * pct / 100 / 50) * 50`, with a minimum of 300.
- The existing logic does the rest: `was` comes from `breakdown[0]`, so the card shows
  a crossed-out was-price and the VDP shows the breakdown rows, as for new cars.
- `_build/inventory.json` is not edited. Demos (no badge) are untouched.
- New vehicle field `priceDrop` (number, `originalPrice - price`, `null` when there is
  no `originalPrice`). It goes in `pageContext.vehicle` and in the VDP URL right after
  `originalPrice`. It is page-owned like every vehicle param: incoming values are
  overwritten or stripped.

## Consequences

- The used VDPs (36/36) and new VDPs (53/53) now carry `originalPrice` and `priceDrop`,
  so the price-drop nudge can fire on used cars.
- The used reductions are fabricated. Anyone reading the site or the context must be
  told (README, PAGE-CONTEXT.md). They will disagree with the live dealer site.
- The root `inventory.json` export does not change: it has no previous-price field.
- If a future scrape provides real used prior prices (`was` or `breakdown`), they win
  automatically, because the block only fills gaps.
- Renaming or removing `priceDrop` needs a new ADR.

## Alternatives considered

- **Write the reductions into `_build/inventory.json`.** Rejected: it would mix
  fabricated values into the scraped source with nothing marking them, and a re-scrape
  would wipe them silently.
- **`random` with a fixed seed.** Rejected: values would shift whenever the order or
  number of listings changed. A per-stock hash is stable per car.
- **Lower `price` instead of inventing a higher previous price.** Rejected: it would
  change the selling price, the export and the filter results.
- **No `priceDrop` param; consumers subtract.** Rejected: the nudge wants the amount
  directly, and URL-only consumers would need two params plus arithmetic.
