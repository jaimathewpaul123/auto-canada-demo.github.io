/* Capital mock site - light interactivity only (nav, filters, sort, view toggle) */
(function () {
  // mobile nav
  var tog = document.querySelector('.navtoggle');
  if (tog) tog.addEventListener('click', function () {
    document.querySelector('.mainnav').classList.toggle('open');
  });

  var grid = document.getElementById('results');
  if (!grid) return;
  var cards = [].slice.call(grid.querySelectorAll('.vcard'));
  var countEl = document.getElementById('resultCount');

  function activeFilters() {
    var f = {};
    document.querySelectorAll('.facet input:checked').forEach(function (i) {
      (f[i.dataset.key] = f[i.dataset.key] || []).push(i.value);
    });
    return f;
  }

  function apply() {
    var f = activeFilters(), shown = 0;
    cards.forEach(function (c) {
      var ok = Object.keys(f).every(function (k) {
        return f[k].indexOf(c.dataset[k] || '') > -1;
      });
      c.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    if (countEl) countEl.textContent = shown;
    var pager = document.querySelector('.pager');
    if (pager) pager.style.display = shown === cards.length ? '' : 'none';
  }

  document.querySelectorAll('.facet input').forEach(function (i) {
    i.addEventListener('change', apply);
  });

  var clear = document.getElementById('clearFilters');
  if (clear) clear.addEventListener('click', function () {
    document.querySelectorAll('.facet input:checked').forEach(function (i) { i.checked = false; });
    apply();
  });

  // sort
  var sort = document.getElementById('sortOrder');
  if (sort) sort.addEventListener('change', function () {
    var v = this.value;
    var sorted = cards.slice().sort(function (a, b) {
      var pa = +a.dataset.pricenum, pb = +b.dataset.pricenum;
      var ya = +a.dataset.year,     yb = +b.dataset.year;
      var ka = +a.dataset.kmnum,    kb = +b.dataset.kmnum;
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
  });

  // grid / list view
  document.querySelectorAll('.viewtog button').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.viewtog button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      grid.closest('.srp-main').classList.toggle('vlist', b.dataset.view === 'list');
    });
  });
})();

/* announcement bar dismiss */
(function () {
  var b = document.getElementById('annbar');
  if (!b) return;
  var x = b.querySelector('.annclose');
  if (x) x.addEventListener('click', function () { b.classList.add('hide'); });
})();

/* hero carousel */
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

/* VDP gallery: clicking a thumb promotes it to the main image */
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
