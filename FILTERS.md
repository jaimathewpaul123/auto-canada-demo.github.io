# Inventory filter URL contract

Every sidebar filter on the three search pages writes its state into the query
string, and any such URL loaded directly restores that state and applies it.
Built so another application can read the current selection straight off the URL,
or drive this page by constructing one.

Applies to `/new/inventory/search.html`, `/demos/search.html`, `/used/search.html`,
`/pages/clearance.html` and `/pages/electric.html`.

## Multi-select facets

Comma-separated. Values **OR** within one param, **AND** across params.
Values are the exact facet labels, URL-encoded.

| Sidebar filter | Query param | Example |
|---|---|---|
| Category | `category` | `category=SUV,Trucks` |
| Brand | `brand` | `brand=Jeep,RAM` |
| Model | `model` | `model=Compass,Cherokee` |
| Year | `year` | `year=2026,2025` |
| Trim | `trim` | `trim=Sport,North` |
| Options | `options` | `options=GPS%20Navigation` |
| Transmission | `transmission` | `transmission=Auto.` |
| Drive train | `drivetrain` | `drivetrain=Four-wheel%20drive` |
| Fuel | `fuel` | `fuel=Gas,Diesel` |
| Engine | `engine` | `engine=3.6L%20Pentastar%20VVT%20V6%20w/ESS` |
| Exterior Colour | `exteriorColour` | `exteriorColour=White,Black` |
| Interior Colour | `interiorColour` | `interiorColour=Black` |
| Doors | `doors` | `doors=4` |
| Cylinders | `cylinders` | `cylinders=6` |

## Ranges

Inclusive on both ends. Plain integers — CAD for price, kilometres for mileage.
No thousands separators, no currency symbol. Either bound may be sent alone.

| Filter | Params | Example |
|---|---|---|
| Price | `priceRangeLow`, `priceRangeHigh` | `priceRangeLow=13000&priceRangeHigh=15000` |
| Mileage | `mileageRangeLow`, `mileageRangeHigh` | `mileageRangeLow=0&mileageRangeHigh=80000` |

## Result count

| Param | Value |
|---|---|
| `resultCount` | Number of vehicle cards matching the active filters: the same number as the "(N)" in the page heading. Not the page size |

- **Always written** on these pages: on load, on every filter change and after
  "Clear all". An unfiltered page carries the full count.
- **Page-owned, output only.** An incoming `resultCount` is ignored and overwritten
  with the real count, so `resultCount=999` in a link is corrected on load. It
  cannot be used to drive the page.
- **Not a filter.** Sort, view and compare changes leave it unchanged.
- Other pages (home, VDPs, other content pages) strip it from the URL.
- Also in `window.pageContext.resultCount`
  ([PAGE-CONTEXT.md](PAGE-CONTEXT.md#resultcount)).

Real example, used SUVs up to $20,000 (5 of the 36 used cars):

```
/used/search.html?pageType=used&inventoryType=used&category=SUV&priceRangeHigh=20000&resultCount=5
```

Decision record: [docs/adr/0004-result-count-in-url.md](docs/adr/0004-result-count-in-url.md).

## View state

| Control | Param | Values |
|---|---|---|
| Sort | `sort` | `price-asc`, `price-desc`, `year-desc`, `year-asc`, `km-asc` |
| Layout | `view` | `list` (grid is the default and is never written) |

## Rules

- An absent param means **no constraint** on that filter.
- The query string always starts with the page's context params
  (`pageType`, `inventoryType`, `pageName`; see
  [PAGE-CONTEXT.md](PAGE-CONTEXT.md#context-in-the-query-string)). Those are not
  filters, and they are ignored on load.
- Filter params are written only while active, so an unfiltered page has only the
  context params and the full `resultCount`, e.g.
  `/used/search.html?pageType=used&inventoryType=used&resultCount=36`.
  "Clear all" removes filter params but keeps the context params, `sort` and `view`,
  and resets `resultCount` to the full count.
- Multiple values are joined with a literal comma; each value is URL-encoded on
  its own, so a comma *inside* a label is sent as `%2C`
  (`options=Sun%2C%20Sound%20%26%20NAV%20Group`). A fully encoded list
  (`brand=Jeep%2CRAM`) is also accepted on load.
- Param order in the URL is fixed (context params, then facets, then ranges,
  then [`resultCount`](#result-count), then sort/view, then the
  [compare params](#compare)), so do not rely on it
  matching the order filters were clicked.
- The URL updates via `history.replaceState` — it changes live without adding
  browser history entries, so Back leaves the page rather than stepping back
  through filter changes.
- Option counts in the sidebar recalculate against every *other* active filter,
  so a count shows how many results that option would add to the current view.
  Options that would return nothing are dimmed.

## Example

```
/used/search.html?pageType=used&inventoryType=used&brand=Jeep,RAM&category=SUV&priceRangeLow=13000&priceRangeHigh=45000&resultCount=5&sort=price-asc
```

Reading it from another application:

```js
const p = new URLSearchParams(location.search);
const brands = p.get('brand')?.split(',') ?? [];      // ['Jeep','RAM']
const lo     = p.get('priceRangeLow');                // '13000'
const hi     = p.get('priceRangeHigh');               // '45000'
const n      = Number(p.get('resultCount'));          // matching cards
```

## Compare

Vehicle cards have a "Compare" checkbox on the three search pages and on
`/pages/clearance.html` and `/pages/electric.html`. The home page carousels have
none, and pages without compare checkboxes drop any `compare`/`compareStock` params.
While at least one car is ticked, a bar above the cards shows "Compare: N of 4
selected" with a **Clear compare** button. It unticks every car and removes both
compare params; filter params are untouched. The filters' "Clear all" does not
clear the compare selection.
The selection is carried in two params, which always come last in the query string.

| Param | Value |
|---|---|
| `compare` | The selected vehicles' compare names, in the order they were ticked |
| `compareStock` | The matching stock numbers, in the same order |

- **Compare name** is `{year} {make} {model} {trim}`, where `{trim}` is the card's
  trim text before the first `|`, trimmed, and left out when empty:
  `Sport | Forward Collision Warning` gives `2025 Jeep Compass Sport`, and the
  untrimmed MINI gives `2017 MINI Cooper Hardtop`. Each card carries it as
  `data-compare-name`, next to `data-stock`.
- **Encoding** is the same as the facets: values joined with a literal comma, each
  value `encodeURIComponent`-ed on its own, so a comma inside a value is `%2C`.
- **Written only when 2 or more are selected.** With 0 or 1 ticked, neither param
  is in the URL. They update via `history.replaceState`, like the filters.
- **Maximum 4.** With 4 ticked, every other compare checkbox on the page is disabled,
  greyed out, and titled "You can compare up to 4 vehicles". Unticking one
  re-enables them.
- **Independent of the filters.** A filter change keeps the compare params and a
  compare change keeps the filters. "Clear all" leaves the compare selection
  alone. A ticked car hidden by a filter stays ticked and stays in the URL.
- **Restored by stock.** On load, only `compareStock` is read: matching cards are
  ticked in that order, unknown stocks are dropped, and anything past 4 is ignored.
  The page then rewrites both params from the cards it ticked, so a stale or edited
  `compare` is corrected, the same way the context params are. Names are not unique
  (the new inventory has eleven `2026 Jeep Compass North`), so `compare` is for
  display and `compareStock` is the key.

Example, two real used vehicles (the MINI has no trim):

```
/used/search.html?pageType=used&inventoryType=used&resultCount=36&compare=2017%20MINI%20Cooper%20Hardtop,2020%20Toyota%20C-HR%20LE&compareStock=17A7269,XC1882A
```

```js
const p = new URLSearchParams(location.search);
const stocks = p.get('compareStock')?.split(',') ?? [];   // ['17A7269','XC1882A']
const names  = p.get('compare')?.split(',') ?? [];        // ['2017 MINI Cooper Hardtop','2020 Toyota C-HR LE']
```

The same selection is in `window.pageContext.compare`
([PAGE-CONTEXT.md](PAGE-CONTEXT.md#compare)). Decision record:
[docs/adr/0003-compare-selection-in-url.md](docs/adr/0003-compare-selection-in-url.md).

## Keeping markup and script in sync

Each search page emits the param-to-attribute mapping the generator used:

```html
<script>window.FACET_MAP={"category":"cat","brand":"make", ...};</script>
```

`js/site.js` reads that map rather than hard-coding it, so adding a facet in
`_build/gen.py` (`FACET_DEFS`) is enough — the script picks it up automatically.
