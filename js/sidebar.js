/* Capital Chrysler Dodge Jeep Ram - mock site: filter sidebar range sliders.

   Presentation only. Each price / mileage range facet keeps its two number
   inputs (data-bound="low|high"), which remain the single source of truth for
   the filter engine in js/site.js and for the URL params
   (priceRangeLow/High, mileageRangeLow/High). This file adds a dual-handle
   slider under them, like the live site, that simply writes those inputs and
   fires the same `input` event a keystroke would. A handle at the end of the
   track clears its input (= no bound), so dragging back to the ends leaves
   the URL as it was. Loaded after site.js, so URL state is already restored. */
(function () {
  var facets = document.querySelector('.facets');
  if (!facets) return;
  var countEl = document.getElementById('resultCount');
  var sliders = [];

  function fmt(n) { return Number(n).toLocaleString('en-US'); }

  [].slice.call(facets.querySelectorAll('.rangeopts')).forEach(function (box) {
    var lo = box.querySelector('input[data-bound="low"]');
    var hi = box.querySelector('input[data-bound="high"]');
    if (!lo || !hi) return;
    var min = Number(lo.min), max = Number(lo.max), step = Number(lo.step) || 1;
    var money = /^price/.test(lo.dataset.param);
    var unit = function (n) { return money ? '$' + fmt(n) : fmt(n) + 'km'; };
    var name = (box.closest('.facet').querySelector('summary') || {}).textContent || '';

    var wrap = document.createElement('div');
    wrap.className = 'rslider';
    wrap.innerHTML = '<div class="rs-track"><div class="rs-fill"></div></div>';
    function knob(cls, label) {
      var r = document.createElement('input');
      r.type = 'range'; r.className = cls; r.min = min; r.max = max; r.step = step;
      r.tabIndex = 0; r.setAttribute('aria-label', name + ' ' + label + ' slider');
      wrap.appendChild(r);
      return r;
    }
    var rLo = knob('rs-lo', 'minimum'), rHi = knob('rs-hi', 'maximum');
    var fill = wrap.firstChild.firstChild;
    var cap = document.createElement('p');
    cap.className = 'rcap';
    var row = box.querySelector('.rangerow');
    row.parentNode.insertBefore(wrap, row.nextSibling);
    wrap.parentNode.insertBefore(cap, wrap.nextSibling);

    function cur(inp, dflt) {
      var v = inp.value.trim();
      return v === '' || isNaN(Number(v)) ? dflt : Math.min(max, Math.max(min, Number(v)));
    }
    function sync() {
      var a = cur(lo, min), b = cur(hi, max);
      rLo.value = Math.min(a, b); rHi.value = Math.max(a, b);
      var span = max - min || 1;
      fill.style.left = ((rLo.value - min) / span * 100) + '%';
      fill.style.right = ((max - rHi.value) / span * 100) + '%';
      cap.innerHTML = '<b>' + unit(Math.min(a, b)) + ' - ' + unit(Math.max(a, b)) + '</b> (' +
        (countEl ? countEl.textContent : '') + ')';
    }
    function push(r, inp, edge) {
      if (r === rLo && +rLo.value > +rHi.value) rLo.value = rHi.value;
      if (r === rHi && +rHi.value < +rLo.value) rHi.value = rLo.value;
      var v = +r.value === edge ? '' : String(r.value);
      if (inp.value === v) return;
      inp.value = v;
      inp.dispatchEvent(new Event('input', { bubbles: true }));
    }
    rLo.addEventListener('input', function () { push(rLo, lo, min); sync(); });
    rHi.addEventListener('input', function () { push(rHi, hi, max); sync(); });
    sliders.push(sync);
    sync();
  });

  if (!sliders.length) return;
  function syncAll() { sliders.forEach(function (f) { f(); }); }
  // Typing in the inputs, chips, "Clear all" and URL restores all end in the
  // filter engine rewriting #resultCount, so that is our cue to resync.
  document.addEventListener('input', function (ev) {
    if (ev.target.matches('.facet input[data-bound]')) syncAll();
  });
  if (countEl && window.MutationObserver) {
    new MutationObserver(syncAll).observe(countEl, { childList: true, characterData: true, subtree: true });
  }
})();
