# Page context contract

Every page says what kind of page it is, and a vehicle detail page (VDP) also
carries the vehicle it shows. Built so another application can tell where it is
and what the shopper is looking at, either from the URL alone or by reading a
JS object on the page. Once loaded, every page writes its context into the query
string, so the URL alone is enough.

Filter params are defined in [FILTERS.md](FILTERS.md). This document reuses them.
Decision record: [docs/adr/0002-page-context-contract.md](docs/adr/0002-page-context-contract.md).

## Context in the query string

On load, every page rewrites its own URL with `history.replaceState` (no new
history entry) so the query string leads with its context. A consumer that reads
only the URL can take everything from the query string, without matching paths.

Param order is fixed. Each value is encoded with `encodeURIComponent`, and a
`null` or empty value is left out rather than written empty.

1. `pageType`: every page.
2. `inventoryType`: search pages and VDPs.
3. `pageName`: `content` pages.
4. VDPs only, the vehicle, in this order. Where a field is also a filter, the param
   uses the [FILTERS.md](FILTERS.md) name, so a VDP URL reads like a filter set
   pinned to one car:

   | Param | `vehicle` field |
   |---|---|
   | `vehicleId`, `vin`, `stock` | `id`, `vin`, `stock` |
   | `year`, `brand`, `model`, `trim` | `year`, `make`, `model`, `trim` |
   | `price`, `originalPrice`, `priceDrop`, `mileage` | same names |
   | `category` | `bodyStyle` |
   | `exteriorColour`, `interiorColour`, `engine`, `transmission`, `drivetrain`, `fuel`, `doors`, `cylinders` | same names |

   `imageUrl`, `url` and `badge` are not written.
5. Pages with the filter sidebar: the filter params, then `resultCount`, then `sort`
   and `view`, as in [FILTERS.md](FILTERS.md). "Clear all" removes the filters but
   never the context params, so an unfiltered search page still carries
   `?pageType=…&inventoryType=…&resultCount=<full count>`. `resultCount` is the number
   of cards matching the filters ([FILTERS.md](FILTERS.md#result-count)); the page
   owns it, overwrites any incoming value, and strips it on every other page.
6. Pages with vehicle cards: `compare` and `compareStock`, last, and only while 2 or
   more cars are ticked ([FILTERS.md](FILTERS.md#compare)). The page owns these too:
   it restores the selection from `compareStock` and rewrites both.

On pages without the filter sidebar, any other params (`utm_source`, …) are kept
after the context params, and
`#hash` is kept on every page.

### The page corrects its own context params

The context params belong to the page, not the link. Incoming `pageType`,
`inventoryType` and `pageName`, and on a VDP every vehicle param, are ignored as
input and overwritten with the true values, so an edited or stale URL is corrected
on load. `/used/search.html?pageType=home` becomes
`/used/search.html?pageType=used&inventoryType=used`. On a search page, `year`,
`brand`, `model` and so on are still filters: only on a VDP are they the vehicle.

A consumer can therefore trust the context params only after the page has loaded
and run `js/site.js`. A link as typed may be stale.

### One URL per pageType

These are the real generated pages.

| pageType | URL after load |
|---|---|
| `home` | `/index.html?pageType=home` |
| `new` | `/new/inventory/search.html?pageType=new&inventoryType=new&resultCount=53` |
| `used` | `/used/search.html?pageType=used&inventoryType=used&category=SUV&priceRangeHigh=20000&resultCount=5` |
| `demo` | `/demos/search.html?pageType=demo&inventoryType=demo&resultCount=6&sort=price-asc` |
| `content` | `/pages/service.html?pageType=content&pageName=service` |
| `content` (with filters) | `/pages/clearance.html?pageType=content&pageName=clearance&category=Truck&resultCount=8` |

VDPs, one per inventory type:

```
/new/inventory/2026-Jeep-Compass-id13263693.html?pageType=vdp&inventoryType=new&vehicleId=13263693&vin=3C4NJDAN5TT208774&stock=6JC8774-NEW&year=2026&brand=Jeep&model=Compass&trim=Sport%20%7C%20Forward%20Collision%20Warning&price=30745&originalPrice=36995&priceDrop=6250&mileage=18&category=SUV&exteriorColour=White&interiorColour=Black&engine=EC1%202.0L%20DOHC%20I-4%20DI%20turbo%20engine%20w%2FESS&transmission=Auto.&drivetrain=Four-wheel%20drive&fuel=Gas&doors=4&cylinders=4

/used/2017-MINI-Cooper_Hardtop-id14428691.html?pageType=vdp&inventoryType=used&vehicleId=14428691&vin=WMWXU1C32H2F77269&stock=17A7269&year=2017&brand=MINI&model=Cooper%20Hardtop&price=13900&originalPrice=14750&priceDrop=850&mileage=72018&category=Cars&exteriorColour=Grey&engine=Intercooled%20Turbo%20Premium%20Unleaded%20I-3%201.5%20L%2F91&transmission=Auto.&drivetrain=Front-wheel%20drive&fuel=Gas&doors=4&cylinders=3

/demos/2025-Jeep-Compass-id13402526.html?pageType=vdp&inventoryType=demo&vehicleId=13402526&vin=3C4NJDAN7ST625358&stock=LD5JC5358-DEMO&year=2025&brand=Jeep&model=Compass&trim=Sport%20%7C%20Forward%20Collision%20Warning&price=28900&mileage=2025&category=SUV&exteriorColour=Blue&interiorColour=Black&engine=Intercooled%20Turbo%20Regular%20Gasoline%20I-4%202.0%20L%2F122&transmission=Auto.&drivetrain=Four-wheel%20drive&fuel=Gas&doors=4&cylinders=4
```

The used MINI has no `trim` or `interiorColour` (both `null`), and the demo has no
`originalPrice` or `priceDrop`, so those params are absent. Used-car reductions are
demo values generated by `_build/gen.py`, not real prices
([ADR 0005](docs/adr/0005-demo-used-price-reductions.md)).

Reading it:

```js
const p = new URLSearchParams(location.search);
p.get('pageType');                         // 'vdp'
p.get('inventoryType');                    // 'new'
Number(p.get('price'));                    // 30745
p.get('trim');                             // 'Sport | Forward Collision Warning'
```

## Detecting page type from the path

This still holds and is the fallback when the page has not run (for example a
link seen before it is opened). Match the path against these rules in order. The query string and `#hash` play no part.

| Path | pageType | inventoryType |
|---|---|---|
| `/` or `/index.html` | `home` | `null` |
| `/new/inventory/search.html` | `new` | `new` |
| `/used/search.html` | `used` | `used` |
| `/demos/search.html` | `demo` | `demo` |
| `/(new/inventory\|used\|demos)/<slug>-id<digits>.html` | `vdp` | from the segment: `new/inventory` is `new`, `used` is `used`, `demos` is `demo` |
| `/pages/<name>.html` | `content` | `null` |

```js
const VDP = /^\/(new\/inventory|used|demos)\/[^/]+-id(\d+)\.html$/;
const SEG = { 'new/inventory': 'new', used: 'used', demos: 'demo' };
const m = location.pathname.match(VDP);
// m ? { pageType: 'vdp', inventoryType: SEG[m[1]], vehicleId: m[2] } : ...
```

VDP slugs mirror the real site, e.g. `/new/inventory/2026-Jeep-Compass-id13263693.html`
or `/used/2017-MINI-Cooper_Hardtop-id14428691.html`. Treat the slug as opaque:
only `-id<digits>.html` is contractual, and the digits are the vehicle `id`.

## `window.pageContext`

The generator emits it as an inline `<script>` in `<head>`, so it exists before
any other script runs. The same values are mirrored on `<body>`:

```html
<body data-page-type="vdp" data-inventory-type="new">
```

`data-inventory-type` is an empty string where `inventoryType` is `null`.

| Field | Type | Present on |
|---|---|---|
| `pageType` | `"home"` `"new"` `"used"` `"demo"` `"vdp"` `"content"` | every page |
| `inventoryType` | `"new"` `"used"` `"demo"` or `null` | every page. Set on search pages and VDPs, `null` elsewhere |
| `pageName` | string, the file name without `.html` | `content` pages only |
| `vehicle` | object or `null` | object on VDPs only |
| `filters` | object or `null` | object wherever the filter sidebar runs, `null` elsewhere |
| `resultCount` | number | listing pages only (the search pages, clearance, electric): cards matching the active filters. Absent elsewhere |
| `compare` | array | pages with compare checkboxes only: the search pages, clearance and electric. Absent elsewhere, including home |

### `vehicle`

Missing values are `null`, never `""` or `0`.

| Field | Type | Notes |
|---|---|---|
| `id`, `vin`, `stock` | string | `id` matches the `-id<digits>` in the URL |
| `year` | number | |
| `make`, `model`, `trim` | string | `trim` is the full trim line, options included (`"Sport \| Forward Collision Warning"`) |
| `price` | number | CAD, the selling price |
| `originalPrice` | number or `null` | CAD, the pre-discount price. `null` unless it is higher than `price` |
| `priceDrop` | number or `null` | CAD, `originalPrice - price` (e.g. `6250`). `null` whenever `originalPrice` is `null`. On used cars this is a demo value ([ADR 0005](docs/adr/0005-demo-used-price-reductions.md)) |
| `mileage` | number | km |
| `exteriorColour`, `interiorColour`, `bodyStyle`, `engine`, `transmission`, `drivetrain`, `fuel` | string or `null` | `bodyStyle` is the inventory Category (`SUV`, `Cars`, `Trucks`, ...) |
| `doors`, `cylinders` | number or `null` | |
| `imageUrl` | string | absolute URL of the main photo |
| `url` | string | site-relative path of this VDP |
| `badge` | string or `null` | e.g. `"Reduced Price"` |

### `filters`

The active filters, keyed by the [FILTERS.md](FILTERS.md) query params:
arrays of strings for multi-select facets, numbers for range bounds, plus
`sort` and `view`. Only active filters appear, so an unfiltered page has `{}`.
`view` appears only as `"list"`, as in the URL.

The generated HTML always holds `{}`. `js/site.js` fills it from the URL before
`pagecontext:ready` fires. Besides the three search pages, `pages/clearance.html`
and `pages/electric.html` run the same filter sidebar. They are `content` pages,
but `filters` is an object there too.

### `resultCount`

The number of vehicle cards matching the active filters, the same as the "(N)" in
the heading and the `resultCount` URL param. The generated HTML holds the
unfiltered count; `js/site.js` recomputes it on load (before `pagecontext:ready`)
and on every filter change, before `pagecontext:change` fires, so the event's
`detail.resultCount` is already the new count. Used SUVs up to $20,000 give `5`.

### `compare`

The cars ticked for comparison, in the order they were ticked, as
`[{"name": "...", "stock": "..."}]`. `name` is the compare name defined in
[FILTERS.md](FILTERS.md#compare). It mirrors the URL: an empty array until 2 or more
are ticked, at most 4 entries. The generated HTML holds `[]`, and `js/site.js`
fills it from `compareStock` before `pagecontext:ready` fires.

## Examples

Home (`/index.html`):

```json
{"pageType":"home","inventoryType":null,"vehicle":null,"filters":null}
```

Search (`/used/search.html?category=SUV&priceRangeHigh=20000&sort=price-asc&view=list`), after `pagecontext:ready`:

```json
{"pageType":"used","inventoryType":"used","vehicle":null,
 "filters":{"category":["SUV"],"priceRangeHigh":20000,"sort":"price-asc","view":"list"},
 "resultCount":5,"compare":[]}
```

Same page with two cars ticked (`…&compare=2017%20MINI%20Cooper%20Hardtop,2020%20Toyota%20C-HR%20LE&compareStock=17A7269,XC1882A`):

```json
"compare":[{"name":"2017 MINI Cooper Hardtop","stock":"17A7269"},
           {"name":"2020 Toyota C-HR LE","stock":"XC1882A"}]
```

Content (`/pages/service.html`):

```json
{"pageType":"content","inventoryType":null,"pageName":"service","vehicle":null,"filters":null}
```

VDP (`/new/inventory/2026-Jeep-Compass-id13263693.html`):

```json
{
  "pageType": "vdp",
  "inventoryType": "new",
  "vehicle": {
    "id": "13263693", "vin": "3C4NJDAN5TT208774", "stock": "6JC8774-NEW",
    "year": 2026, "make": "Jeep", "model": "Compass",
    "trim": "Sport | Forward Collision Warning",
    "price": 30745, "originalPrice": 36995, "priceDrop": 6250, "mileage": 18,
    "exteriorColour": "White", "interiorColour": "Black", "bodyStyle": "SUV",
    "engine": "EC1 2.0L DOHC I-4 DI turbo engine w/ESS", "transmission": "Auto.",
    "drivetrain": "Four-wheel drive", "fuel": "Gas", "doors": 4, "cylinders": 4,
    "imageUrl": "https://imagescdn.d2cmedia.ca/mbb5aca2e98ff1173a6f08a2036346b853/5431/13263693/1/Jeep-Compass-2026.jpg",
    "url": "/new/inventory/2026-Jeep-Compass-id13263693.html",
    "badge": "Reduced Price"
  },
  "filters": null
}
```

## Events

Both are dispatched on `window` as a `CustomEvent`. `event.detail` is `window.pageContext`.

| Event | When |
|---|---|
| `pagecontext:ready` | Once, on `DOMContentLoaded`, after the filter sidebar has read the URL. Every page |
| `pagecontext:change` | When the active filters change: a facet, range, sort, view, chip, or "Clear all". `resultCount` is already updated when it fires. Also when a compare tick changes `compare`, so ticking the first car fires nothing (it stays `[]`) and ticking the second does. Not fired on load, and not fired when a change leaves `filters` and `compare` the same |

## Reading it from another application

```js
function onContext(ctx) {
  if (ctx.pageType === 'vdp') show(ctx.vehicle.year, ctx.vehicle.model, ctx.vehicle.price);
  else if (ctx.filters) refine(ctx.inventoryType, ctx.filters);
}

// A script that loads after DOMContentLoaded misses `ready`, so read the object first.
if (document.readyState === 'loading') {
  window.addEventListener('pagecontext:ready', e => onContext(e.detail), { once: true });
} else {
  onContext(window.pageContext);
}
window.addEventListener('pagecontext:change', e => onContext(e.detail));
```

## Where it comes from

`_build/gen.py` builds the object (`page_context`, `vehicle_context`) and places
each VDP at its inventory record's `url` (`vdp_path`). The events live at the end
of `js/site.js`, and `publishFilters` in the filter engine keeps `filters` current.
`SiteUrl` at the top of `js/site.js` writes the context params from
`window.pageContext`, and appends the compare params through its `tail` hook, which
the compare block right after it sets. `card` and `compare_name` in `_build/gen.py`
emit the checkbox and `data-compare-name`/`data-stock`. The filter engine's `writeUrl` calls it on search-type pages, adding `resultCount`
(it also sets `SiteUrl.rewrite`, which the compare block calls so `resultCount`
keeps its slot),
and the page-context block calls it on every other page.
