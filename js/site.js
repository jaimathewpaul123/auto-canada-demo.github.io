/* Capital CDJR mock site
   nav, announcement bar, hero carousel, vehicle gallery,
   and URL-synced inventory filtering. */

/* ================================================================
   Context params in the query string (PAGE-CONTEXT.md, ADR 0002).
   Every URL leads with the page's own context, in a fixed order:
     pageType, inventoryType, pageName, then on VDPs the vehicle params.
   Listing pages (filter sidebar) write resultCount after the filter
   ranges and before sort/view; it is owned by the page and always
   rewritten from the real match count, and stripped everywhere else.
   Pages with vehicle cards end the query with the compare params
   (compare, compareStock), supplied through SiteUrl.tail by the
   Compare block below; those are owned by the page too.
   The page owns these params: whatever the loaded URL said is ignored
   and overwritten with the true values from window.pageContext.
   ================================================================ */
var SiteUrl = (function () {
  // [query param, vehicle field]. Params that also exist as filters use the
  // FILTERS.md name, so a VDP URL reads like a filter set pinned to one car.
  var VEHICLE = [
    ['vehicleId', 'id'], ['vin', 'vin'], ['stock', 'stock'],
    ['year', 'year'], ['brand', 'make'], ['model', 'model'], ['trim', 'trim'],
    ['price', 'price'], ['originalPrice', 'originalPrice'], ['priceDrop', 'priceDrop'],
    ['mileage', 'mileage'],
    ['category', 'bodyStyle'], ['exteriorColour', 'exteriorColour'],
    ['interiorColour', 'interiorColour'], ['engine', 'engine'],
    ['transmission', 'transmission'], ['drivetrain', 'drivetrain'],
    ['fuel', 'fuel'], ['doors', 'doors'], ['cylinders', 'cylinders']
  ];
  var BASE = ['pageType', 'inventoryType', 'pageName'];
  var COMPARE = ['compare', 'compareStock'];
  var RESULT_COUNT = 'resultCount';

  function ctx() { return window.pageContext || {}; }
  function isVdp() { return ctx().pageType === 'vdp'; }

  /* Param names this page owns (and so never reads as input). */
  function owned() {
    var o = {};
    BASE.forEach(function (k) { o[k] = 1; });
    if (isVdp()) VEHICLE.forEach(function (kv) { o[kv[0]] = 1; });
    // Always owned: pages with compare re-add them via the tail hook; pages
    // without compare checkboxes (home) drop them.
    COMPARE.forEach(function (k) { o[k] = 1; });
    // Always owned: listing pages rewrite it from the real count (the filter
    // engine's writeUrl); every other page drops it.
    o[RESULT_COUNT] = 1;
    return o;
  }

  /* ["pageType=vdp", "inventoryType=new", ...] in contract order, values encoded. */
  function contextPairs() {
    var c = ctx(), out = [];
    function add(k, v) {
      if (v === null || v === undefined || v === '') return;
      out.push(k + '=' + encodeURIComponent(String(v)));
    }
    BASE.forEach(function (k) { add(k, c[k]); });
    if (isVdp() && c.vehicle) VEHICLE.forEach(function (kv) { add(kv[0], c.vehicle[kv[1]]); });
    return out;
  }

  /* Replace the URL (no history entry) with context params first, then `rest`,
     then whatever the tail hook supplies (the compare params). */
  function replace(rest) {
    var qs = contextPairs().concat(rest || [], api.tail ? api.tail() : []).join('&');
    history.replaceState(history.state, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
  }

  /* Raw "k=v" pairs from the current query that the page does not own. */
  function foreignPairs() {
    var o = owned();
    return location.search.replace(/^\?/, '').split('&').filter(function (pair) {
      if (!pair) return false;
      var i = pair.indexOf('='), k = i > -1 ? pair.slice(0, i) : pair;
      try { k = decodeURIComponent(k); } catch (e) {}
      return !o[k];
    });
  }

  /* Rewrite the whole URL from current state. The filter engine replaces this
     on listing pages (so resultCount keeps its slot before sort/view); elsewhere
     it keeps the foreign params and re-adds the owned ones. */
  function rewrite() { replace(foreignPairs()); }

  var api = { owned: owned, contextPairs: contextPairs, replace: replace,
              foreignPairs: foreignPairs, rewrite: rewrite,
              filterEngine: false, tail: null };
  return api;
})();

/* ================================================================
   Compare checkboxes on vehicle cards (FILTERS.md, "Compare").
     ?compare=2025%20Jeep%20Compass%20Sport,2026%20Jeep%20Wrangler%20Sport
     &compareStock=LD5JC5358-DEMO,6JW1234-NEW
   Selection order, max 4, written only while 2+ are selected, always
   last in the query. Restored by stock; `compare` is rewritten from
   the cards, so a stale or edited name is corrected on load.
   Runs before the filter engine so its first URL write keeps them.
   ================================================================ */
(function () {
  var MAX = 4, TIP = 'You can compare up to ' + MAX + ' vehicles';
  var boxes = [].slice.call(document.querySelectorAll('.vcard .cmp-box'));
  if (!boxes.length) return;

  var cars = {};        // stock -> { name, stock }
  function stockOf(b) { return b.closest('.vcard').dataset.stock; }
  boxes.forEach(function (b) {
    var c = b.closest('.vcard');
    cars[c.dataset.stock] = { name: c.dataset.compareName, stock: c.dataset.stock };
  });
  var sel = [];         // stocks, in selection order

  function active() { return sel.length >= 2 ? sel.map(function (s) { return cars[s]; }) : []; }

  /* "compare=a,b" / "compareStock=x,y": literal commas between values,
     each value encoded on its own, exactly like the filter params. */
  SiteUrl.tail = function () {
    var list = active();
    if (!list.length) return [];
    function join(f) { return list.map(function (c) { return encodeURIComponent(c[f]); }).join(','); }
    return ['compare=' + join('name'), 'compareStock=' + join('stock')];
  };

  var bar = document.getElementById('compareBar');

  function renderBar() {
    if (!bar) return;
    bar.hidden = !sel.length;
    if (!sel.length) { bar.innerHTML = ''; return; }
    var hint = sel.length < 2 ? ' &middot; select one more to compare' : '';
    bar.innerHTML = '<span class="cmpbar-txt"><b>Compare:</b> ' + sel.length + ' of ' + MAX +
      ' selected' + hint + '</span>' +
      '<button type="button" class="cmp-clear">Clear compare</button>';
  }

  function render() {
    renderBar();
    var full = sel.length >= MAX;
    boxes.forEach(function (b) {
      var on = sel.indexOf(stockOf(b)) > -1, off = full && !on;
      b.checked = on;
      b.disabled = off;
      var lab = b.closest('.cmp');
      lab.classList.toggle('dis', off);
      if (off) lab.title = b.title = TIP;
      else { lab.removeAttribute('title'); b.removeAttribute('title'); }
    });
  }

  var last = null;
  function publish(notify) {
    var list = active().map(function (c) { return { name: c.name, stock: c.stock }; });
    var key = JSON.stringify(list);
    var ctx = window.pageContext = window.pageContext || {};
    ctx.compare = list;
    if (key === last) return;
    last = key;
    if (notify) window.dispatchEvent(new CustomEvent('pagecontext:change', { detail: ctx }));
  }

  function readStocks() {
    var raw = null;
    location.search.replace(/^\?/, '').split('&').forEach(function (pair) {
      var i = pair.indexOf('=');
      if (i > 0 && pair.slice(0, i) === 'compareStock') raw = pair.slice(i + 1);
    });
    if (!raw) return [];
    function dec(x) { try { return decodeURIComponent(x.replace(/\+/g, ' ')); } catch (e) { return x; } }
    // Literal commas separate values; otherwise one stock, or a fully encoded list.
    var list = raw.indexOf(',') > -1 ? raw.split(',').map(dec)
             : (cars[dec(raw)] ? [dec(raw)] : dec(raw).split(','));
    var out = [];
    list.forEach(function (s) {
      s = s.trim();
      if (cars[s] && out.indexOf(s) < 0 && out.length < MAX) out.push(s);
    });
    return out;
  }

  document.addEventListener('change', function (ev) {
    var b = ev.target;
    if (!b.matches || !b.matches('.vcard .cmp-box')) return;
    var s = stockOf(b), i = sel.indexOf(s);
    if (b.checked && i < 0 && sel.length < MAX) sel.push(s);
    else if (!b.checked && i > -1) sel.splice(i, 1);
    render();
    // Keep filters, resultCount, sort, view; the tail re-adds compare.
    SiteUrl.rewrite();
    publish(true);
  });

  if (bar) bar.addEventListener('click', function (ev) {
    if (!ev.target.closest('.cmp-clear')) return;
    sel = [];
    render();
    SiteUrl.rewrite();
    publish(true);
  });

  sel = readStocks();
  render();
  publish(false);
  // The URL itself is rewritten by the filter engine's first writeUrl, or by
  // the page-context block on pages without the sidebar (the home page).
})();

/* ---------------------------------------------------------- mobile nav */
(function () {
  var tog = document.querySelector('.navtoggle');
  if (tog) tog.addEventListener('click', function () {
    document.querySelector('.mainnav').classList.toggle('open');
  });
})();

/* ------------------------------------------------- announcement bar */
(function () {
  var b = document.getElementById('annbar');
  if (!b) return;
  var x = b.querySelector('.annclose');
  if (x) x.addEventListener('click', function () { b.classList.add('hide'); });
})();

/* ---------------------------------------------------- hero carousel */
(function () {
  var hero = document.getElementById('hero');
  if (!hero) return;
  var slides = [].slice.call(hero.querySelectorAll('.slide'));
  var dots   = [].slice.call(hero.querySelectorAll('.herodots button'));
  var i = 0, timer;

  function show(n) {
    i = (n + slides.length) % slides.length;
    slides.forEach(function (s, k) { s.classList.toggle('on', k === i); });
    dots.forEach(function (d, k) { d.classList.toggle('on', k === i); });
  }
  function start() { timer = setInterval(function () { show(i + 1); }, 6000); }
  function reset() { clearInterval(timer); start(); }

  hero.querySelector('.prev').addEventListener('click', function () { show(i - 1); reset(); });
  hero.querySelector('.next').addEventListener('click', function () { show(i + 1); reset(); });
  dots.forEach(function (d) {
    d.addEventListener('click', function () { show(+d.dataset.i); reset(); });
  });
  hero.addEventListener('mouseenter', function () { clearInterval(timer); });
  hero.addEventListener('mouseleave', start);
  start();
})();

/* --------------------------------------------------- VDP gallery */
(function () {
  var strip = document.getElementById('vdpThumbs'),
      main  = document.getElementById('vdpMain');
  if (!strip || !main) return;
  strip.addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    strip.querySelectorAll('button').forEach(function (x) { x.classList.remove('on'); });
    b.classList.add('on');
    main.src = b.dataset.src;
  });
})();

/* ================================================================
   Inventory filtering, driven by and reflected in the URL.

   Multi-select facets      ?brand=Jeep,RAM&category=SUV
     comma separated, OR within a param, AND across params
   Ranges (inclusive)       ?priceRangeLow=13000&priceRangeHigh=15000
                            ?mileageRangeLow=0&mileageRangeHigh=80000
   View state               ?sort=price-asc&view=list

   window.FACET_MAP (emitted by the generator) maps each query param to
   the data-* attribute holding that value on a vehicle card, so the
   markup and this script can never drift apart.
   ================================================================ */
(function () {
  var grid = document.getElementById('results');
  if (!grid) return;

  var FACETS = window.FACET_MAP || {};
  var RANGES = {
    price:   { low: 'priceRangeLow',   high: 'priceRangeHigh',   attr: 'pricenum' },
    mileage: { low: 'mileageRangeLow', high: 'mileageRangeHigh', attr: 'kmnum'    }
  };

  var cards   = [].slice.call(grid.querySelectorAll('.vcard'));
  var countEl = document.getElementById('resultCount');
  var chipsEl = document.getElementById('activeFilters');
  var emptyEl = document.getElementById('noResults');
  var sortEl  = document.getElementById('sortOrder');

  function boxes()  { return [].slice.call(document.querySelectorAll('.facet input[type=checkbox]')); }
  function ranges() { return [].slice.call(document.querySelectorAll('.facet input[data-bound]')); }

  function selected() {
    var out = {};
    boxes().forEach(function (b) {
      if (b.checked) (out[b.dataset.param] = out[b.dataset.param] || []).push(b.value);
    });
    return out;
  }
  function bounds() {
    var out = {};
    ranges().forEach(function (i) {
      var raw = i.value.trim();
      if (raw !== '' && !isNaN(Number(raw))) out[i.dataset.param] = Number(raw);
    });
    return out;
  }

  function cardValues(card, param) {
    return (card.dataset[FACETS[param]] || '').split('|').filter(Boolean);
  }
  function matches(card, sel, bnd, skipParam) {
    for (var p in sel) {
      if (p === skipParam || !sel[p].length) continue;
      var have = cardValues(card, p);
      var hit = sel[p].some(function (v) { return have.indexOf(v) > -1; });
      if (!hit) return false;
    }
    for (var r in RANGES) {
      var cfg = RANGES[r], n = Number(card.dataset[cfg.attr] || 0);
      if (bnd[cfg.low]  !== undefined && n < bnd[cfg.low])  return false;
      if (bnd[cfg.high] !== undefined && n > bnd[cfg.high]) return false;
    }
    return true;
  }

  /* counts reflect every OTHER active filter */
  function updateCounts(sel, bnd) {
    boxes().forEach(function (b) {
      var p = b.dataset.param;
      var n = cards.filter(function (c) {
        return matches(c, sel, bnd, p) && cardValues(c, p).indexOf(b.value) > -1;
      }).length;
      var cnt = b.parentNode.querySelector('.cnt');
      if (cnt) cnt.textContent = n;
      b.parentNode.classList.toggle('zero', n === 0 && !b.checked);
    });
  }

  function renderChips(sel, bnd) {
    if (!chipsEl) return;
    var chips = [];
    Object.keys(sel).forEach(function (p) {
      sel[p].forEach(function (v) {
        chips.push('<button type="button" class="chip" data-kind="facet" data-param="' + p +
                   '" data-value="' + v.replace(/"/g, '&quot;') + '">' + v + ' &times;</button>');
      });
    });
    Object.keys(bnd).forEach(function (p) {
      var label = p.replace('RangeLow', ' from ').replace('RangeHigh', ' up to ');
      var money = p.indexOf('price') === 0 ? '$' : '';
      chips.push('<button type="button" class="chip" data-kind="range" data-param="' + p + '">' +
                 label + money + bnd[p].toLocaleString() + ' &times;</button>');
    });
    chipsEl.innerHTML = chips.length
      ? chips.join('') + '<button type="button" class="chip clearall">Clear all</button>'
      : '';
    chipsEl.hidden = !chips.length;
  }

  function writeUrl(sel, bnd) {
    // Built by hand so multi-values keep a literal comma (brand=Jeep,RAM);
    // each value is encoded on its own, so a comma inside a label stays %2C.
    var p = [];
    function add(k, v) { p.push(k + '=' + v); }
    Object.keys(FACETS).forEach(function (k) {
      if (sel[k] && sel[k].length) add(k, sel[k].map(encodeURIComponent).join(','));
    });
    Object.keys(bnd).forEach(function (k) { add(k, bnd[k]); });
    // Page-owned: always the real number of matching cards, never the input.
    add('resultCount', shownCount);
    if (sortEl && sortEl.value) add('sort', encodeURIComponent(sortEl.value));
    var v = document.querySelector('.viewtog button.on');
    if (v && v.dataset.view === 'list') add('view', 'list');
    // Context params always lead (SiteUrl), including after "Clear all".
    SiteUrl.replace(p);
  }

  function readUrl() {
    var p = new URLSearchParams(location.search);
    // Split on literal commas before decoding so labels containing a comma
    // survive; also accept a fully-encoded list (brand=Jeep%2CRAM).
    // Context params (pageType, inventoryType, pageName) belong to the page,
    // not the shopper, so they are never read as filters.
    var own = SiteUrl.owned();
    var rawQs = {};
    location.search.replace(/^\?/, '').split('&').forEach(function (pair) {
      var i = pair.indexOf('=');
      if (i > 0) {
        var k = decodeURIComponent(pair.slice(0, i));
        if (!own[k]) rawQs[k] = pair.slice(i + 1);
      }
    });
    function dec(s) { try { return decodeURIComponent(s.replace(/\+/g, ' ')); } catch (e) { return s; } }
    var known = {};
    boxes().forEach(function (b) { (known[b.dataset.param] = known[b.dataset.param] || {})[b.value] = 1; });
    function values(param) {
      var raw = rawQs[param];
      if (!raw) return [];
      // Literal commas separate values (our own format).
      if (raw.indexOf(',') > -1) return raw.split(',').map(dec);
      // Otherwise a single label that contains a comma, or a fully encoded list.
      var whole = dec(raw);
      return (known[param] || {})[whole] ? [whole] : whole.split(',');
    }
    boxes().forEach(function (b) {
      b.checked = values(b.dataset.param).indexOf(b.value) > -1;
    });
    ranges().forEach(function (i) {
      var raw = own[i.dataset.param] ? null : p.get(i.dataset.param);
      i.value = (raw === null || raw === '') ? '' : raw;
    });
    if (sortEl && p.get('sort')) sortEl.value = p.get('sort');
    if (p.get('view') === 'list') setView('list');
    [].slice.call(document.querySelectorAll('.facet')).forEach(function (d) {
      var live = d.querySelector('input[type=checkbox]:checked') ||
                 [].slice.call(d.querySelectorAll('input[data-bound]'))
                   .some(function (i) { return i.value !== ''; });
      if (live) d.open = true;
    });
  }

  function sortNow(v) {
    var sorted = cards.slice().sort(function (a, b) {
      var pa = +a.dataset.pricenum, pb = +b.dataset.pricenum,
          ya = +a.dataset.year,     yb = +b.dataset.year,
          ka = +a.dataset.kmnum,    kb = +b.dataset.kmnum;
      switch (v) {
        case 'price-asc':  return pa - pb;
        case 'price-desc': return pb - pa;
        case 'year-desc':  return yb - ya;
        case 'year-asc':   return ya - yb;
        case 'km-asc':     return ka - kb;
        default:           return 0;
      }
    });
    sorted.forEach(function (c) { grid.appendChild(c); });
  }
  function setView(mode) {
    document.querySelectorAll('.viewtog button').forEach(function (x) {
      x.classList.toggle('on', x.dataset.view === mode);
    });
    var main = grid.closest('.srp-main');
    if (main) main.classList.toggle('vlist', mode === 'list');
  }

  /* Active filters in the shape of window.pageContext.filters (PAGE-CONTEXT.md):
     same keys and order as the URL; arrays for facets, numbers for ranges. */
  function activeFilters(sel, bnd) {
    var f = {};
    Object.keys(FACETS).forEach(function (k) { if (sel[k] && sel[k].length) f[k] = sel[k].slice(); });
    Object.keys(bnd).forEach(function (k) { f[k] = bnd[k]; });
    if (sortEl && sortEl.value) f.sort = sortEl.value;
    var v = document.querySelector('.viewtog button.on');
    if (v && v.dataset.view === 'list') f.view = 'list';
    return f;
  }
  var lastFilters = null;
  var shownCount = cards.length;  // cards matching the active filters
  function publishFilters(sel, bnd, notify) {
    var f = activeFilters(sel, bnd), key = JSON.stringify(f);
    if (key === lastFilters) return;
    lastFilters = key;
    var ctx = window.pageContext = window.pageContext || {};
    ctx.filters = f;
    if (notify) window.dispatchEvent(new CustomEvent('pagecontext:change', { detail: ctx }));
  }

  function apply(sync) {
    var sel = selected(), bnd = bounds(), shown = 0;
    cards.forEach(function (c) {
      var ok = matches(c, sel, bnd, null);
      c.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    shownCount = shown;
    // Set before publishFilters so pagecontext:change carries the new count.
    (window.pageContext = window.pageContext || {}).resultCount = shown;
    if (countEl) countEl.textContent = shown;
    if (emptyEl) emptyEl.hidden = shown !== 0;
    var pager = document.querySelector('.pager');
    if (pager) pager.style.display = (shown === cards.length) ? '' : 'none';
    updateCounts(sel, bnd);
    renderChips(sel, bnd);
    if (sync !== false) writeUrl(sel, bnd);
    publishFilters(sel, bnd, sync !== false);
  }

  function clearAll() {
    boxes().forEach(function (b) { b.checked = false; });
    ranges().forEach(function (i) { i.value = ''; });
    apply();
  }

  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (t.matches('.facet input[type=checkbox]') || t.matches('.facet input[data-bound]')) apply();
    else if (t === sortEl) { sortNow(t.value); apply(); }
  });
  document.addEventListener('input', function (ev) {
    if (ev.target.matches('.facet input[data-bound]')) apply();
  });
  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (t.id === 'clearFilters' || t.id === 'clearFilters2' || t.classList.contains('clearall')) {
      clearAll(); return;
    }
    var chip = t.closest && t.closest('.chip[data-param]');
    if (chip) {
      if (chip.dataset.kind === 'range') {
        ranges().forEach(function (i) { if (i.dataset.param === chip.dataset.param) i.value = ''; });
      } else {
        boxes().forEach(function (b) {
          if (b.dataset.param === chip.dataset.param && b.value === chip.dataset.value) b.checked = false;
        });
      }
      apply(); return;
    }
    var vb = t.closest && t.closest('.viewtog button');
    if (vb) { setView(vb.dataset.view); apply(); }
  });

  SiteUrl.filterEngine = true;
  SiteUrl.rewrite = function () { writeUrl(selected(), bounds()); };
  readUrl();
  if (sortEl && sortEl.value) sortNow(sortEl.value);
  apply(false);
  writeUrl(selected(), bounds());
})();

/* ================================================================
   Page context for other applications (see PAGE-CONTEXT.md).
   window.pageContext is emitted inline by the generator; the filter
   engine above has already filled in `filters` from the URL by the
   time pagecontext:ready fires.
   ================================================================ */
(function () {
  window.pageContext = window.pageContext || {
    pageType: document.body.dataset.pageType || null,
    inventoryType: document.body.dataset.inventoryType || null,
    vehicle: null, filters: null
  };
  // Pages without the filter sidebar rewrite their URL here so it leads with
  // the true context params; stale ones are dropped, other params are kept.
  // (The filter engine has already done this on search-type pages.)
  if (!SiteUrl.filterEngine) {
    SiteUrl.replace(SiteUrl.foreignPairs());
    delete window.pageContext.resultCount;
  }
  function ready() {
    window.dispatchEvent(new CustomEvent('pagecontext:ready', { detail: window.pageContext }));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
