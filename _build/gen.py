# -*- coding: utf-8 -*-
"""Static site generator for the Capital CDJR mock site."""
import json, os, re, html, collections, hashlib

SRC  = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.dirname(SRC)
INV  = json.load(open(os.path.join(SRC, 'inventory.json')))

DEALER   = 'Capital Chrysler Dodge Jeep Ram'
ADDRESS  = '1311 101 ST. SW, Edmonton, AB T6X 1A1'
SALES    = '587-416-1056'
SERVICE  = '587-854-6920'
LOGO     = 'https://www.capitaljeep.com/images/Logo/Capital-Logo.webp'
# Optimy chat plugin, installed on every page (QA build).
OPTIMY_LICENSE_KEY = '0b2d101c-60bc-11eb-9752-75ceaf0e3ecf'
OPTIMY_SCRIPT      = 'https://delonghi.qa.optimycdn.com/optimy.js'
# Reported to Optimy as guest_hostname; must be a domain registered for the tenant.
OPTIMY_GUEST_HOSTNAME = 'https://optimy-qa.myshopify.com/'
MAPS     = ('https://www.google.ca/maps/dir/?api=1&destination=Capital%2BChrysler'
            '%2BDodge%2BJeep%2BRam%2C1311+101+ST.+SW%2CEdmonton%2CAB%2CT6X+1A1')

# ---------------------------------------------------------------- data tidy
def km_num(desc):
    m = re.match(r'([\d,]+)\s*KM', desc or '')
    return int(m.group(1).replace(',', '')) if m else 0

def price_num(p):
    return int(re.sub(r'[^\d]', '', p)) if p else 0

def fmt(n):
    return '{:,}'.format(n)

# ---- demo price reductions for used cars
# Every used listing carries a 'Reduced Price' badge but the scrape has no previous
# price, so the VDP showed no reduction and pageContext.vehicle.originalPrice was null.
# Give each such car a DEMO reduction of 3-8%, picked from a hash of its stock number
# (not `random`) so every regeneration produces the same numbers. The selling price is
# untouched; only a 'Previous Price' / 'Price Reduction' breakdown is added, in the same
# shape as the new cars' breakdown. These are not real prices (docs/adr/0005).
def demo_reduction(v):
    price = price_num(v.get('price'))
    pct = 3 + int(hashlib.md5(v['stock'].encode('utf-8')).hexdigest(), 16) % 6   # 3..8
    drop = max(300, int(round(price * pct / 5000.0)) * 50)   # nearest $50, min $300
    return [['Previous Price', fmt(price + drop)], ['Price Reduction', '-' + fmt(drop)]]

for v in INV.get('used', []):
    if (v.get('badge') == 'Reduced Price' and not v.get('was') and not v.get('breakdown')
            and price_num(v.get('price'))):
        v['breakdown'] = demo_reduction(v)

for cond, rows in INV.items():
    for v in rows:
        v['cond']    = cond
        v['desc']    = re.sub(r'\s+\.', '.', (v.get('desc') or '')).strip().strip(',')
        v['kmnum']   = km_num(v['desc'])
        v['km']      = '{:,}'.format(v['kmnum'])
        v['pricenum'] = price_num(v.get('price'))
        bd = v.get('breakdown') or []
        v['was'] = v.get('was') or (bd[0][1] if bd else '')
        if price_num(v['was']) <= v['pricenum']:
            v['was'] = ''
        s = v.get('spec') or {}
        v['cat']   = s.get('Category', '')
        v['trans'] = s.get('Transmission', '')
        v['drive'] = s.get('Drive train', '')
        v['fuel']  = s.get('Fuel', '')
        v['ext']   = s.get('Exterior Colour', '')
        v['int']   = s.get('Interior Colour', '')
        v['doors'] = s.get('Doors', '')
        v['cyl']   = s.get('Cylinders', '')
        v['engine']= s.get('Engine', '')
        v['name']  = '{} {} {}'.format(v['year'], v['make'], v['model']).strip()
        parts = [p.strip() for p in (v.get('trim') or '').split('|') if p.strip()]
        v['trimbase'] = parts[0] if parts else ''
        v['options']  = parts[1:]

# ---------------------------------------------------------------- VDP paths
# VDPs live at the record's `url`, mirroring the real site:
#   /new/inventory/<year>-<Make>-<Model>-id<id>.html, /used/..., /demos/...
# The URL alone therefore identifies a VDP and its inventory type (see PAGE-CONTEXT.md).
COND_SEG = {'new': 'new/inventory', 'demos': 'demos', 'used': 'used'}

def _slug(s):
    return re.sub(r'[^A-Za-z0-9]+', '_', s or '').strip('_')

def vdp_path(v):
    """Site-relative path (no leading slash) of a vehicle's detail page."""
    seg = COND_SEG[v['cond']]
    u = (v.get('url') or '').lstrip('/')
    if re.fullmatch(re.escape(seg) + r'/[A-Za-z0-9_.-]+-id' + re.escape(v['id']) + r'\.html', u):
        return u
    return '{}/{}-{}-{}-id{}.html'.format(seg, _slug(v['year']), _slug(v['make']),
                                          _slug(v['model']), v['id'])

for cond, rows in INV.items():
    for v in rows:
        v['path'] = vdp_path(v)

ALL = INV['new'] + INV['demos'] + INV['used']
BY_ID = {v['id']: v for v in ALL}
assert len({v['path'] for v in ALL}) == len(ALL), 'duplicate VDP paths'

def e(s):
    return html.escape(s or '', quote=True)


BANNERS = [
    ('images/banner2/REFS-69189_Stellantis_JeepConquest_WB.webp',
     'Make the switch to Jeep &mdash; up to $3,000 on select new Jeep models', 'pages/offers.html'),
    ('images/banner4/REFS-69545_EmployeePricing_Event_2000 x 555.webp',
     'Employee Pricing Event', 'new/inventory/search.html'),
    ('images/banner3/REFS-63323_Stellantis_27RumbleBee_WB.webp',
     '2027 RAM 1500 Rumble Bee', 'new/inventory/search.html'),
    ('images/banner5/RAM_OEM_2000 x 555.webp',
     'RAM offers', 'pages/offers.html'),
    ('images/banner1/Ford-Dodge-VW Central West_FOps_TSW_Web Banner_2000x555_AUG26-2.webp',
     'Tire and service offers', 'pages/service.html'),
]
BANNER_BASE = 'https://www.capitaljeep.com/'

# ---------------------------------------------------------------- nav
def nav_model_links(cond, limit=9):
    seen = collections.OrderedDict()
    for v in INV[cond]:
        seen.setdefault('{} {}'.format(v['make'], v['model']), v['id'])
    return list(seen.items())[:limit]

NEW_BY_MAKE = collections.OrderedDict()
for v in INV['new']:
    NEW_BY_MAKE.setdefault(v['make'], collections.OrderedDict())[v['model']] = v['year']

NAV = [
    ('About', 'pages/about.html', [('', [
        ('About the dealership', 'pages/about.html'),
        ('Our team',             'pages/ourteam.html'),
        ('After sales service',  'pages/our-services.html'),
        ('Latest news',          'pages/news.html'),
        ('Hours & directions',   'pages/hours.html'),
        ('Contact us',           'pages/about.html'),
    ])]),
    ('Service &amp; Parts', 'pages/service.html', [('', [
        ('Book an appointment', 'pages/service-appointment.html'),
        ('Service specials',    'pages/service-specials.html'),
        ('Order parts',         'pages/parts.html'),
        ('Tire finder',         'pages/tires.html'),
        ('Accessories',         'pages/accessories.html'),
        ('Parts catalogue',     'pages/parts-catalogue.html'),
    ])]),
    ('Financing', 'pages/financing.html', [('', [
        ('Apply for financing',   'pages/credit.html'),
        ('Payment calculator',    'pages/calculator.html'),
        ('Value your trade-in',   'pages/trade-in.html'),
        ('Sell us your vehicle',  'pages/sell.html'),
    ])]),
    ('Offers', 'pages/offers.html', [('', [
        ('Manufacturer incentives', 'pages/offers.html'),
        ('New vehicle promotions',  'pages/promotions.html'),
        ('Employee pricing event',  'pages/employee-pricing.html'),
        ('Service specials',        'pages/service-specials.html'),
    ])]),
    ('Clearance', 'pages/clearance.html', None),
    ('Electric',  'pages/electric.html', [('', [
        ('All electric &amp; hybrid', 'pages/electric.html'),
        ('Jeep 4xe plug-in hybrid',   'pages/electric.html'),
        ('All-electric models',       'pages/electric.html'),
        ('Charging &amp; range',      'pages/electric.html'),
    ])]),
    ('Pre-Owned', 'used/search.html', None),
    ('Demos',     'demos/search.html', None),
    ('New Vehicles', 'new/inventory/search.html', None),
]

# build the mega-menus that need generated data
_pre = [('Browse', [('All pre-owned inventory', 'used/search.html')] +
        [('Used ' + mk, 'used/search.html') for mk in ['Chrysler', 'Dodge', 'Jeep', 'Ram']])]
_used_models = nav_model_links('used', 16)
for i in range(0, len(_used_models), 6):
    chunk = _used_models[i:i + 6]
    _pre.append(('Popular models' if i == 0 else '&nbsp;',
                 [(n, BY_ID[vid]['path']) for n, vid in chunk]))
NAV[6] = ('Pre-Owned', 'used/search.html', _pre)

_demo = [('Browse', [('All demo vehicles', 'demos/search.html'),
                     ('Jeep demos', 'demos/search.html'),
                     ('RAM demos', 'demos/search.html')]),
         ('In stock now', [('{} {}'.format(v['year'], v['model']), v['path'])
                           for v in INV['demos'][:6]])]
NAV[7] = ('Demos', 'demos/search.html', None)

_new = [('Browse', [('All new inventory', 'new/inventory/search.html'),
                    ('Clearance', 'pages/clearance.html'),
                    ('Electric & hybrid', 'pages/electric.html')])]
for mk, models in NEW_BY_MAKE.items():
    _new.append((mk, [('{} {}'.format(yr, md), 'new/inventory/search.html')
                      for md, yr in list(models.items())[:7]]))
NAV[8] = ('New Vehicles', 'new/inventory/search.html', _new[:5])

NAV.reverse()   # the live site runs New Vehicles first, About last

# Sub-menu entries under the non-inventory menus are labels only: every one of them
# navigates to its parent page, because those are the only pages that exist.
for _i, (_label, _href, _drop) in enumerate(NAV):
    if _drop and _label not in ('Pre-Owned', 'Demos', 'New Vehicles'):
        NAV[_i] = (_label, _href,
                   [(_t, [(_lbl, _href) for _lbl, _ in _links]) for _t, _links in _drop])

# ---------------------------------------------------------------- chrome
def nav_html(root, active):
    out = []
    for label, href, drop in NAV:
        cls = ' class="active"' if label.replace('&amp;', '&') == active else ''
        caret = '<span class="caret">&#9660;</span>' if drop else ''
        out.append('<li{}><a href="{}{}">{}{}</a>'.format(cls, root, href, label, caret))
        if drop:
            multi = len(drop) > 1
            out.append('<div class="drop{}">'.format(' cols' if multi else ''))
            for title, links in drop:
                if multi:
                    out.append('<div><h4>{}</h4>'.format(title))
                for t, h in links:
                    out.append('<a href="{}{}">{}</a>'.format(root, h, t))
                if multi:
                    out.append('</div>')
            out.append('</div>')
        out.append('</li>')
    return '\n'.join(out)

HOURS = [('Sales', 'Mon&ndash;Thu 9:00&ndash;20:00 &middot; Fri 9:00&ndash;18:00 &middot; Sat 8:30&ndash;18:00 &middot; Sun 11:00&ndash;16:00'),
         ('Service', 'Mon&ndash;Fri 7:00&ndash;18:00 &middot; Closed weekends'),
         ('Parts', 'Mon&ndash;Fri 7:30&ndash;18:00 &middot; Closed weekends'),
         ('Express Lane', 'Mon&ndash;Fri 7:00&ndash;18:00 &middot; Sat 8:00&ndash;14:00')]

def page_context(page_type, inventory_type=None, page_name=None, vehicle=None, filters=None,
                 result_count=None, compare=None):
    ctx = collections.OrderedDict([('pageType', page_type), ('inventoryType', inventory_type)])
    if page_name is not None:
        ctx['pageName'] = page_name
    ctx['vehicle'] = vehicle
    ctx['filters'] = filters
    # Only listing pages carry `resultCount`: the unfiltered card count here,
    # kept current by js/site.js as filters change.
    if result_count is not None:
        ctx['resultCount'] = result_count
    # Only pages with vehicle cards carry `compare` (filled by js/site.js from the URL).
    if compare is not None:
        ctx['compare'] = compare
    return ctx

def ctx_script(ctx):
    js = json.dumps(ctx, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return '<script>window.pageContext={};</script>'.format(js)

def body_attrs(ctx):
    return ' data-page-type="{}" data-inventory-type="{}"'.format(
        e(ctx['pageType']), e(ctx['inventoryType'] or ''))

def head(title, root, active, desc='', ctx=None):
    ctx = ctx or page_context('content')
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {dealer}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="{root}css/site.css">
{ctx}
</head>
<body{battrs}>
<div class="annbar" id="annbar">
  <div class="wrap"><a href="{root}new/inventory/search.html">Employee Pricing On Now!</a></div>
  <button class="annclose" type="button" aria-label="Close">&times;</button>
</div>

<header class="masthead"><div class="wrap">
  <a class="brand" href="{root}index.html"><img src="{logo}" alt="{dealer}"></a>
  <div class="dealerinfo">
    <p class="dname">{dealer}</p>
    <p class="daddr"><a href="{maps}" target="_blank" rel="noopener">&#10148; {addr}</a></p>
    <table class="dphones">
      <tr><td>Sales:</td><td><a href="tel:{sales}">{sales}</a></td></tr>
      <tr><td>Service:</td><td><a href="tel:{service}">{service}</a></td></tr>
      <tr><td>Parts:</td><td><a href="tel:{sales}">{sales}</a></td></tr>
    </table>
  </div>
</div></header>

<div class="mainnav">
  <button class="navtoggle" type="button">&#9776; &nbsp;Menu</button>
  <div class="wrap">
    <ul>
{nav}
    </ul>
    <form class="navsearch" onsubmit="return false">
      <input type="search" placeholder="Search for a vehicle" aria-label="Search for a vehicle">
      <button type="submit" aria-label="Search">&#128269;</button>
    </form>
  </div>
</div>
'''.format(title=e(title), dealer=DEALER, desc=e(desc or title), root=root, maps=MAPS,
           addr=ADDRESS, sales=SALES, service=SERVICE, logo=LOGO, nav=nav_html(root, active),
           ctx=ctx_script(ctx), battrs=body_attrs(ctx))

def foot(root):
    hrs = '\n'.join('<tr><td>{}</td><td>{}</td></tr>'.format(a, b) for a, b in HOURS)
    def col(title, links):
        return '<div><h4>{}</h4>{}</div>'.format(
            title, ''.join('<a href="{}{}">{}</a>'.format(root, h, t) for t, h in links))
    return '''<footer>
<div class="fmain"><div class="wrap"><div class="fgrid">
{c1}
{c2}
{c3}
{c4}
<div class="fcontact">
  <h4>Visit us</h4>
  <p><a href="{maps}" target="_blank" rel="noopener">{addr}</a></p>
  <p>Sales<br><a class="num" href="tel:{sales}">{sales}</a></p>
  <p>Service<br><a class="num" href="tel:{service}">{service}</a></p>
  <table class="hours">{hrs}</table>
  <div class="fsoc"><a href="{root}pages/about.html">f</a><a href="{root}pages/about.html">&#9654;</a><a href="{root}pages/about.html">&#9679;</a></div>
</div>
</div></div></div>
<div class="fbar"><div class="wrap">
  <span>&copy; 2026 {dealer}. Mock site for demonstration only &mdash; not affiliated with the real dealership.</span>
  <span><a href="{root}pages/about.html">Contact &amp; hours</a>
    &middot; <a href="?resetDemo=1" class="reset-demo" title="Clear this demo's local and session storage and reload">Reset demo</a></span>
</div></div>
</footer>
<script src="{root}js/site.js"></script>
<script>
  window.OPTIMY_LICENSE_KEY = '{optimy_key}';
  window.OPTIMY_GUEST_HOSTNAME = '{optimy_host}';
</script>
<script src="{optimy_src}"></script>
<optimy-launcher></optimy-launcher>
</body>
</html>'''.format(
        optimy_key=OPTIMY_LICENSE_KEY, optimy_src=OPTIMY_SCRIPT, optimy_host=OPTIMY_GUEST_HOSTNAME,
        c1=col('Buying tools', [('Financing', 'pages/financing.html'),
                                ('Current offers', 'pages/offers.html'),
                                ('Clearance', 'pages/clearance.html')]),
        c2=col('Inventory', [('New vehicles', 'new/inventory/search.html'),
                             ('Demo vehicles', 'demos/search.html'),
                             ('Pre-owned vehicles', 'used/search.html'),
                             ('Electric &amp; hybrid', 'pages/electric.html')]),
        c3=col('Service &amp; parts', [('Service &amp; parts', 'pages/service.html')]),
        c4=col('The dealership', [('About us', 'pages/about.html')]),
        maps=MAPS, addr=ADDRESS, sales=SALES, service=SERVICE, hrs=hrs,
        dealer=DEALER, root=root)

def write(path, body):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(body)
    return path

# ---------------------------------------------------------------- vehicle card
def compare_name(v):
    """'{year} {make} {model} {trim before the first |}', trim part omitted if empty.
    This exact string is what the `compare` URL param carries (FILTERS.md)."""
    first = (v.get('trim') or '').split('|')[0].strip()
    return ' '.join(str(x).strip() for x in [v['year'], v['make'], v['model'], first] if str(x).strip())

def card(v, root, compare=True):
    badge = ''
    if v['cond'] == 'demos':
        badge = '<span class="badge demo">Demo</span>'
    elif v.get('badge'):
        badge = '<span class="badge">{}</span>'.format(e(v['badge']))
    was = '<span class="was">${}</span>'.format(v['was']) if v['was'] else ''
    plus = '<p class="plus">*Plus GST and applicable fees</p>'
    trim = e(v['trim']) or '&nbsp;'
    specbits = ' &middot; '.join(x for x in [
        v['km'] + ' km', v['trans'], v['drive'], v['fuel'],
        ('Ext: ' + v['ext']) if v['ext'] else ''] if x)
    return '''<article class="vcard" data-make="{make}" data-model="{model}" data-year="{year}"
  data-cat="{cat}" data-trim="{trimbase}" data-options="{options}" data-trans="{trans}"
  data-drive="{drive}" data-fuel="{fuel}" data-engine="{engine}" data-ext="{ext}"
  data-int="{intc}" data-doors="{doors}" data-cyl="{cyl}"
  data-pricenum="{pn}" data-kmnum="{kn}"
  data-stock="{stock}" data-compare-name="{cmpname}">
  <div class="imgwrap">
    {badge}
    <a href="{root}{vpath}"><img class="{imgcls}" src="{img}" alt="{alt}" loading="lazy"></a>
    <div class="stockline">Stock: {stock}<br>VIN: {vin}</div>
  </div>
  <div class="body">
    <h3 class="ttl"><a href="{root}{vpath}"><span class="mk">{make}</span> {year} {model}</a></h3>
    <p class="trim">{trim}</p>
    <div class="price"><span class="now">${price}</span>{was}{cmp}</div>
    {plus}
    <div class="specs">{specs}</div>
    <div class="cta">
      <a class="btn btn-red" href="{root}{vpath}">View details</a>
      <a class="btn btn-out" href="{root}{vpath}">Confirm availability</a>
    </div>
  </div>
</article>'''.format(make=e(v['make']), model=e(v['model']), year=e(v['year']), cat=e(v['cat']),
                     trans=e(v['trans']), fuel=e(v['fuel']), ext=e(v['ext']), drive=e(v['drive']),
                     pn=v['pricenum'], kn=v['kmnum'],
                     cmp=('<label class="cmp"><input type="checkbox" class="cmp-box" value="{}"> Compare</label>'.format(e(v['stock'])) if compare else ''),
                     trimbase=e(v['trimbase']), options=e('|'.join(v['options'])),
                     engine=e(v['engine']), intc=e(v['int']),
                     doors=e(v['doors']), cyl=e(v['cyl']),
                     badge=badge, root=root, vpath=v['path'], img=e(v['img']),
                     imgcls='fit' if 'carimages' in v['img'] else '',
                     alt=e(v['name']), stock=e(v['stock']), vin=e(v['vin']),
                     cmpname=e(compare_name(v)),
                     trim=trim, price=e(v['price']), was=was, plus=plus, specs=specbits)

# ---------------------------------------------------------------- facets
# (sidebar label, key on the vehicle record, URL query param, card data-* attribute)
FACET_DEFS = [
    ('Category',        'cat',      'category',       'cat'),
    ('Brand',           'make',     'brand',          'make'),
    ('Model',           'model',    'model',          'model'),
    ('Year',            'year',     'year',           'year'),
    ('Trim',            'trimbase', 'trim',           'trim'),
    ('Options',         'options',  'options',        'options'),
    ('Transmission',    'trans',    'transmission',   'trans'),
    ('Drive train',     'drive',    'drivetrain',     'drive'),
    ('Fuel',            'fuel',     'fuel',           'fuel'),
    ('Engine',          'engine',   'engine',         'engine'),
    ('Exterior Colour', 'ext',      'exteriorColour', 'ext'),
    ('Interior Colour', 'int',      'interiorColour', 'int'),
    ('Doors',           'doors',    'doors',          'doors'),
    ('Cylinders',       'cyl',      'cylinders',      'cyl'),
]
FACET_MAP = {param: attr for _, _, param, attr in FACET_DEFS}

RANGE_DEFS = [
    ('Price',   'pricenum', 'priceRangeLow',   'priceRangeHigh',   '$', '',    500),
    ('Mileage', 'kmnum',    'mileageRangeLow', 'mileageRangeHigh', '',  ' km', 1000),
]

def _vals(v, key):
    """A vehicle's value(s) for a facet key - always a list."""
    x = v.get(key)
    if isinstance(x, list):
        return [i for i in x if i]
    return [x] if x else []

def range_facet(title, lo, hi, p_lo, p_hi, pre, suf, step):
    return ('<details class="facet" open><summary>{t}</summary>'
            '<div class="opts rangeopts"><div class="rangerow">'
            '<input type="number" data-param="{plo}" data-bound="low" min="{lo}" max="{hi}"'
            ' step="{st}" placeholder="{pre}{lo:,}{suf}" aria-label="{t} minimum">'
            '<span class="sep">to</span>'
            '<input type="number" data-param="{phi}" data-bound="high" min="{lo}" max="{hi}"'
            ' step="{st}" placeholder="{pre}{hi:,}{suf}" aria-label="{t} maximum">'
            '</div><p class="rangehint">In stock: {pre}{lo:,}{suf} &ndash; {pre}{hi:,}{suf}</p>'
            '</div></details>').format(t=title, lo=lo, hi=hi, plo=p_lo, phi=p_hi,
                                       pre=pre, suf=suf, st=step)

def facets_html(rows):
    out = ['<aside class="facets"><div class="hd"><span>Refine your search</span>'
           '<button id="clearFilters" type="button">Clear all</button></div>']
    for i, (title, key, param, attr) in enumerate(FACET_DEFS):
        counts = collections.Counter()
        for v in rows:
            for x in _vals(v, key):
                counts[x] += 1
        if not counts:
            continue
        if key == 'year':
            order = sorted(counts.items(), key=lambda x: x[0], reverse=True)
        else:
            order = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        opts = ''.join(
            '<label><input type="checkbox" data-param="{p}" value="{v}">'
            '<span class="lbl">{v}</span><span class="cnt">{c}</span></label>'.format(
                p=param, v=e(val), c=cnt) for val, cnt in order)
        out.append('<details class="facet"{op}><summary>{t}</summary>'
                   '<div class="opts">{o}</div></details>'
                   .format(op=' open' if i < 4 else '', t=title, o=opts))
    for title, key, p_lo, p_hi, pre, suf, step in RANGE_DEFS:
        lo = min(v[key] for v in rows)
        hi = max(v[key] for v in rows)
        out.append(range_facet(title, lo, hi, p_lo, p_hi, pre, suf, step))
    out.append('</aside>')
    return '\n'.join(out)

# ---------------------------------------------------------------- SRP pages
SRP = {
    'new':   dict(path='new/inventory/search.html', root='../../',
                  h1='New Vehicles for sale in Edmonton', active='New Vehicles',
                  crumb=[('New Vehicles', 'new/inventory/search.html')],
                  blurb='Browse the full new Chrysler, Dodge, Jeep and Ram lineup in stock at '
                        'our Edmonton showroom. Employee Pricing is on now.'),
    'demos': dict(path='demos/search.html', root='../',
                  h1='Demo Vehicles for sale in Edmonton', active='Demos',
                  crumb=[('Demos', 'demos/search.html')],
                  blurb='Low-kilometre demonstrator vehicles with the balance of factory warranty, '
                        'priced well below new.'),
    'used':  dict(path='used/search.html', root='../',
                  h1='Pre-Owned Vehicles for sale in Edmonton', active='Pre-Owned',
                  crumb=[('Pre-Owned', 'used/search.html')],
                  blurb='Every pre-owned vehicle is safety inspected and comes with a free '
                        'CARFAX Canada history report.'),
}

# pageType / inventoryType value per inventory key (see PAGE-CONTEXT.md)
INV_TYPE = {'new': 'new', 'demos': 'demo', 'used': 'used'}

SORTS = [('', 'Sort order'), ('price-asc', 'Price: low to high'),
         ('price-desc', 'Price: high to low'), ('year-desc', 'Year: newest first'),
         ('year-asc', 'Year: oldest first'), ('km-asc', 'Mileage: lowest first')]

def srp(cond):
    cfg  = SRP[cond]; root = cfg['root']; rows = INV[cond]
    crumb = ' &rsaquo; '.join(['<a href="{}index.html">Home</a>'.format(root)] +
                              [t for t, h in cfg['crumb']])
    sorts = ''.join('<option value="{}">{}</option>'.format(v, t) for v, t in SORTS)
    cards = '\n'.join(card(v, root) for v in rows)
    pager = ('<nav class="pager">'
             '<span class="dis">&laquo; Prev</span>'
             '<span class="on">1</span><a href="#">2</a><a href="#">3</a>'
             '<a href="#">4</a><span>&hellip;</span><a href="#">Next &raquo;</a>'
             '</nav>')
    body = '''<div class="crumbs"><div class="wrap">{crumb}</div></div>
<div class="wrap"><div class="srp">
{facets}
<div class="srp-main">
  <div class="srp-bar">
    <h1>{h1} <span class="count">(<span id="resultCount">{n}</span>)</span></h1>
    <div class="srp-tools">
      <label for="sortOrder" class="sr">Sort</label>
      <select id="sortOrder">{sorts}</select>
      <span class="viewtog"><button class="on" data-view="grid" type="button">&#9638; Grid</button><button data-view="list" type="button">&#9776; List</button></span>
    </div>
  </div>
  <div id="activeFilters" class="chips" hidden></div>
  <div id="compareBar" class="cmpbar" hidden></div>
  <p style="margin:-8px 0 18px;color:#6b6b6b;font-size:13px;max-width:720px">{blurb}</p>
  <p id="noResults" class="noresults" hidden>No vehicles match these filters.
     <button type="button" id="clearFilters2">Clear all filters</button></p>
  <div class="vgrid g3" id="results">
{cards}
  </div>
  {pager}
</div>
</div></div>
<script>window.FACET_MAP={facetmap};</script>
'''.format(crumb=crumb, facets=facets_html(rows), h1=e(cfg['h1']), n=len(rows),
           sorts=sorts, blurb=e(cfg['blurb']), cards=cards, pager=pager,
           facetmap=json.dumps(FACET_MAP))
    ctx = page_context(INV_TYPE[cond], INV_TYPE[cond], filters={}, result_count=len(rows), compare=[])
    return write(cfg['path'], head(cfg['h1'], root, cfg['active'], cfg['blurb'], ctx) + body + foot(root))

# ---------------------------------------------------------------- VDP
SRP_LINK = {'new': 'new/inventory/search.html', 'demos': 'demos/search.html', 'used': 'used/search.html'}
COND_LBL = {'new': 'New', 'demos': 'Demo', 'used': 'Pre-Owned'}

def _num(s):
    s = re.sub(r'[^\d]', '', s or '')
    return int(s) if s else None

def _txt(s):
    return s if s else None

# ---- demo open recalls
# The scrape has no recall data. To demo the plugin's recall nudge, a few VDPs carry
# a DEMO open-recall count, keyed by vehicle id. Every other car has openRecalls null,
# so the param is absent from its URL (docs/adr/0006).
DEMO_OPEN_RECALLS = {
    '14351116': 1,   # used 2024 Jeep Compass
}

def vehicle_context(v):
    """Typed vehicle record for window.pageContext.vehicle (see PAGE-CONTEXT.md)."""
    km = re.match(r'([\d,]+)\s*KM', v['desc'])
    return collections.OrderedDict([
        ('id', v['id']), ('vin', _txt(v['vin'])), ('stock', _txt(v['stock'])),
        ('year', _num(v['year'])), ('make', _txt(v['make'])), ('model', _txt(v['model'])),
        ('trim', _txt(v['trim'])),
        ('price', _num(v.get('price'))), ('originalPrice', _num(v['was'])),
        ('priceDrop', (_num(v['was']) - _num(v.get('price'))) if v['was'] else None),
        ('mileage', int(km.group(1).replace(',', '')) if km else None),
        ('openRecalls', DEMO_OPEN_RECALLS.get(v['id'])),
        ('exteriorColour', _txt(v['ext'])), ('interiorColour', _txt(v['int'])),
        ('bodyStyle', _txt(v['cat'])), ('engine', _txt(v['engine'])),
        ('transmission', _txt(v['trans'])), ('drivetrain', _txt(v['drive'])),
        ('fuel', _txt(v['fuel'])), ('doors', _num(v['doors'])), ('cylinders', _num(v['cyl'])),
        ('imageUrl', _txt(v['img'])), ('url', '/' + v['path']), ('badge', _txt(v.get('badge'))),
    ])

def vdp(v):
    root = '../' * v['path'].count('/')
    rows = [('Stock number', v['stock']), ('VIN', v['vin']), ('Condition', COND_LBL[v['cond']]),
            ('Body style', v['cat']), ('Mileage', v['km'] + ' km'), ('Engine', v['engine']),
            ('Cylinders', v['cyl']), ('Transmission', v['trans']), ('Drivetrain', v['drive']),
            ('Fuel type', v['fuel']), ('Exterior colour', v['ext']),
            ('Interior colour', v['int']), ('Doors', v['doors'])]
    spec = '\n'.join('<tr><td>{}</td><td>{}</td></tr>'.format(e(a), e(b) or '&mdash;') for a, b in rows)
    fit = ' class="fit"' if 'carimages' in v['img'] else ''
    thumbs = ''.join(
        '<button type="button" class="{on}" data-src="{img}" aria-label="View image {n}">'
        '<img src="{img}" alt="{alt} view {n}" loading="lazy"{fit}></button>'.format(
            on='on' if i == 0 else '', img=e(v['img']), alt=e(v['name']), n=i + 1, fit=fit)
        for i in range(5))
    bd = v.get('breakdown') or []
    if bd:
        lines = ''.join('<div class="row"><span>{}</span><span class="{}">${}</span></div>'
                        .format(e(a), 'neg' if b.startswith('-') else '', e(b.lstrip('-')) if b.startswith('-') else e(b))
                        for a, b in bd)
    else:
        lines = '<div class="row"><span>Retail price</span><span>${}</span></div>'.format(e(v['was'] or v['price']))
    pricebox = ('<div class="pricebox">{}<div class="row tot"><span>Your price</span>'
                '<span>${}</span></div><p style="font-size:11px;color:#6b6b6b;margin:10px 0 0">'
                '*Plus GST and any costs or charges associated with financing.</p></div>'
                ).format(lines, e(v['price']))
    body = '''<div class="crumbs"><div class="wrap">
<a href="{root}index.html">Home</a> &rsaquo; <a href="{root}{srp}">{cl} Vehicles</a> &rsaquo; {name}
</div></div>
<div class="wrap"><div class="vdp">
  <div class="gallery">
    <img id="vdpMain" src="{img}" alt="{name}"{fitmain}>
    <div class="thumbs" id="vdpThumbs">{thumbs}</div>
    <h2 style="margin:26px 0 10px;font-size:19px">Specifications</h2>
    <table class="spectable">{spec}</table>
  </div>
  <div>
    <h1>{year} {make} {model}</h1>
    <p class="sub">{trim}Stock {stock} &middot; VIN {vin}</p>
    {pricebox}
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">
      <a class="btn btn-red" href="{root}pages/about.html">Confirm availability</a>
      <a class="btn btn-dark" href="{root}pages/financing.html">Apply for financing</a>
      <a class="btn btn-out" href="{root}pages/financing.html">Value your trade</a>
    </div>
    <div class="pcard"><h3>Have a question about this vehicle?</h3>
      <p>Call our sales team at <a href="tel:{sales}" style="color:#C30130;font-weight:700">{sales}</a>
      or visit us at {addr}. This is a demo page &mdash; no enquiry is actually sent.</p></div>
  </div>
</div></div>
'''.format(root=root, srp=SRP_LINK[v['cond']], cl=COND_LBL[v['cond']], name=e(v['name']),
           img=e(v['img']), spec=spec, year=e(v['year']), make=e(v['make']), model=e(v['model']),
           thumbs=thumbs, fitmain=fit,
           trim=(e(v['trim']) + ' &middot; ') if v['trim'] else '', stock=e(v['stock']),
           vin=e(v['vin']), pricebox=pricebox, sales=SALES, addr=ADDRESS)
    ctx = page_context('vdp', INV_TYPE[v['cond']], vehicle=vehicle_context(v))
    return write(v['path'],
                 head(v['name'], root, COND_LBL[v['cond']] if v['cond'] != 'new' else 'New Vehicles',
                      '{} for sale at {}'.format(v['name'], DEALER), ctx) + body + foot(root))

# ---------------------------------------------------------------- home page
NEWS = [('Sept 22, 2026', 'The 2027 RAM 1500 Rumble Bee returns',
         'A modern tribute to the 1970s Super Bee, the Rumble Bee package lands this fall with '
         'unique badging, a bespoke interior and an exhaust note to match.'),
        ('Sept 9, 2026', '2027 Jeep Cherokee Trailhawk revealed',
         'Selec-Terrain, a one-inch factory lift and 17-inch off-road wheels headline the '
         'most capable Cherokee yet. Reserve yours at Capital today.'),
        ('Aug 28, 2026', 'Employee Pricing is on now at Capital',
         'For a limited time every eligible new Chrysler, Dodge, Jeep and Ram in our Edmonton '
         'showroom is priced the way our own staff buy.')]

TILES = [('New', 'New Vehicles', 'Shop the full 2026&ndash;2027 lineup', 'new/inventory/search.html'),
         ('Used', 'Pre-Owned', 'Inspected, CARFAX-reported vehicles', 'used/search.html'),
         ('Svc', 'Schedule Service', 'Book your next visit online', 'pages/service.html'),
         ('$', 'Sell or Trade', 'Get a real cash offer in minutes', 'pages/financing.html')]

def home():
    root = ''
    def spread(rows, n):
        """One vehicle per distinct model first, so the row isn't eight of the same car."""
        seen, picked = set(), []
        for v in rows:
            key = (v['make'], v['model'])
            if key not in seen:
                seen.add(key); picked.append(v)
        for v in rows:
            if len(picked) >= n: break
            if v not in picked: picked.append(v)
        return picked[:n]
    featured = spread(INV['new'], 8)
    demos = spread(INV['demos'], 4)
    used = spread(INV['used'], 4)
    tiles = ''.join(
        '<a class="tile" href="{r}{h}"><div class="ico">{i}</div><h3>{t}</h3><p>{p}</p></a>'
        .format(r=root, h=h, i=i, t=t, p=p) for i, t, p, h in TILES)
    news = ''.join(
        '<article class="newscard"><div class="ph"></div><div class="body">'
        '<div class="date">{d}</div><h3>{t}</h3><p>{b}</p></div></article>'
        .format(d=d, t=e(t), b=e(b)) for d, t, b in NEWS)
    slides = '\n'.join(
        '<a class="slide{on}" href="{root}{href}"><img src="{base}{img}" alt="{alt}"'
        ' loading="{lazy}"></a>'.format(
            on=' on' if i == 0 else '', root=root, href=h, base=BANNER_BASE,
            img=img.replace(' ', '%20'), alt=e(alt), lazy='eager' if i == 0 else 'lazy')
        for i, (img, alt, h) in enumerate(BANNERS))
    dots = ''.join('<button type="button" class="{}" data-i="{}" aria-label="Slide {}"></button>'
                   .format('on' if i == 0 else '', i, i + 1) for i in range(len(BANNERS)))
    years = ''.join('<option>{}</option>'.format(y) for y in range(2026, 2004, -1))
    makes = ''.join('<option>{}</option>'.format(m) for m in
                    ['Jeep', 'RAM', 'Dodge', 'Chrysler', 'Ford', 'Chevrolet', 'Toyota',
                     'Honda', 'Hyundai', 'Nissan', 'Volkswagen', 'Other'])
    body = '''<section class="hero" id="hero">
  <div class="slides">{slides}</div>
  <button class="heroarrow prev" type="button" aria-label="Previous">&#10094;</button>
  <button class="heroarrow next" type="button" aria-label="Next">&#10095;</button>
  <div class="herodots">{dots}</div>
</section>

<section class="tradein"><div class="wrap">
  <h2>Get a <strong>free</strong> Trade-In Estimate</h2>
  <form class="tiform" onsubmit="return false">
    <select aria-label="Select year"><option value="">Select year</option>{years}</select>
    <select aria-label="Select make"><option value="">Select make</option>{makes}</select>
    <select aria-label="Select model" class="narrow"><option value="">Select model</option></select>
    <select aria-label="Select trim" class="narrow"><option value="">Select trim</option></select>
    <button class="tibtn" type="submit">Get Started &nbsp;&rarr;</button>
  </form>
  <p class="tipower">Powered by <strong>AutoCanada</strong></p>
</div></section>

<section class="tiles"><div class="wrap"><div class="grid">{tiles}</div></div></section>

<section class="section"><div class="wrap">
  <div class="sec-head"><h2>Featured new vehicles</h2>
    <a href="{r}new/inventory/search.html">View all {nn} new &rsaquo;</a></div>
  <div class="vgrid">{feat}</div>
</div></section>

<section class="section alt"><div class="wrap">
  <div class="sec-head"><h2>Demo vehicles</h2>
    <a href="{r}demos/search.html">View all {nd} demos &rsaquo;</a></div>
  <div class="vgrid">{demo}</div>
</div></section>

<section class="section"><div class="wrap">
  <div class="sec-head"><h2>Recent pre-owned arrivals</h2>
    <a href="{r}used/search.html">View all {nu} pre-owned &rsaquo;</a></div>
  <div class="vgrid">{used}</div>
</div></section>

<section class="section alt"><div class="wrap"><div class="about-grid">
  <div>
    <h2>Proudly serving Edmonton for over 26 years</h2>
    <p>Capital Chrysler Dodge Jeep Ram is a certified five-star retailer with more than 100 staff
       across sales, service, parts and collision. Whether you are shopping your first Wrangler or
       booking a fleet of Ram 3500s in for service, you get the same straightforward treatment.</p>
    <p>Our Express Lane is open six days a week for oil changes and quick maintenance &mdash;
       no appointment needed.</p>
    <a class="btn btn-dark" href="{r}pages/about.html">More about us</a>
    <div class="stats">
      <div class="stat"><div class="n">26+</div><div class="l">Years in Edmonton</div></div>
      <div class="stat"><div class="n">100+</div><div class="l">Team members</div></div>
      <div class="stat"><div class="n">5.0</div><div class="l">Star rated</div></div>
    </div>
  </div>
  <div class="pcard">
    <h3>Opening hours</h3>
    <table class="spectable" style="margin-top:10px">{hrs}</table>
    <a class="btn btn-red" style="margin-top:16px" href="{r}pages/about.html">Get directions</a>
  </div>
</div></div></section>

<section class="section"><div class="wrap">
  <div class="sec-head"><h2>Latest news</h2><a href="{r}pages/about.html">All news &rsaquo;</a></div>
  <div class="vgrid g3">{news}</div>
</div></section>
'''.format(r=root, slides=slides, dots=dots, years=years, makes=makes, tiles=tiles,
           nn=len(INV['new']), nd=len(INV['demos']), nu=len(INV['used']),
           feat='\n'.join(card(v, root, compare=False) for v in featured),
           demo='\n'.join(card(v, root, compare=False) for v in demos),
           used='\n'.join(card(v, root, compare=False) for v in used),
           hrs='\n'.join('<tr><td>{}</td><td>{}</td></tr>'.format(a, b) for a, b in HOURS),
           news=news)
    return write('index.html', head('New &amp; Used Chrysler Dodge Jeep Ram in Edmonton', root, 'Home',
                                    'Chrysler, Dodge, Jeep and Ram dealer in Edmonton.',
                                    page_context('home')) + body + foot(root))

# ---------------------------------------------------------------- content pages
def page(slug, title, sub, active, sections):
    """A real content page. `sections` is a list of raw HTML blocks."""
    root = '../'
    body = ('<div class="pagehead"><div class="wrap"><h1>{t}</h1><p>{s}</p></div></div>\n'
            '<div class="wrap"><div class="prose">\n{b}\n</div></div>\n'
            ).format(t=title, s=sub, b='\n'.join(sections))
    return write('pages/{}.html'.format(slug),
                 head(title, root, active, sub, page_context('content', page_name=slug)) + body + foot(root))

def cards2(items):
    return '<div class="cards2">' + ''.join(
        '<div class="pcard"><h3>{}</h3><p>{}</p></div>'.format(h, p) for h, p in items) + '</div>'

def table(rows):
    return '<table class="spectable">' + ''.join(
        '<tr><td>{}</td><td>{}</td></tr>'.format(a, b) for a, b in rows) + '</table>'

HOURS_TABLE = table(HOURS)

def about_page():
    stats = ('<div class="stats">'
             '<div class="stat"><div class="n">26+</div><div class="l">Years in Edmonton</div></div>'
             '<div class="stat"><div class="n">100+</div><div class="l">Team members</div></div>'
             '<div class="stat"><div class="n">5.0</div><div class="l">Star rated</div></div>'
             '</div>')
    news = ''.join(
        '<h3 style="margin:22px 0 4px;font-size:17px">{t}</h3>'
        '<p style="color:#C30130;font-size:12px;font-weight:700;text-transform:uppercase;'
        'letter-spacing:.6px;margin:0 0 6px">{d}</p><p>{b}</p>'.format(t=e(t), d=d, b=e(b))
        for d, t, b in NEWS)
    return page('about', 'About Capital', 'Edmonton&rsquo;s five-star Chrysler Dodge Jeep Ram retailer',
                'About', [
        '<p>Capital Chrysler Dodge Jeep Ram opened on 101 Street in 1999 and has grown into one of '
        'Alberta&rsquo;s largest Stellantis retailers. Over a hundred people work here across sales, '
        'service, parts and collision, and a good number of them have been with us for more than a '
        'decade.</p>',
        '<p>We hold the manufacturer&rsquo;s highest customer-experience certification, renewed every '
        'year, and our Express Lane runs six days a week so routine maintenance never needs an '
        'appointment.</p>',
        stats,
        '<h2>Our team</h2>',
        cards2([('Sales', 'Fourteen product advisors split across the Jeep, Ram, Dodge and Chrysler '
                          'lines, plus a dedicated commercial and fleet desk.'),
                ('Service', 'Factory-trained technicians, a six-day Express Lane and a loaner fleet '
                            'for longer jobs.'),
                ('Parts', 'Genuine Mopar parts and accessories, ordered direct and usually in hand '
                          'within 24 hours.'),
                ('Collision', 'An in-house body shop that handles insurance claims start to finish.')]),
        '<h2>After sales service</h2>',
        '<p>Scheduled maintenance, diagnostics, warranty work, tire storage and collision repair all '
        'happen on site. Your service history stays with the vehicle, so anything we have touched is '
        'on file the next time it comes in.</p>',
        '<h2>Latest news</h2>', news,
        '<h2 id="hours">Opening hours</h2>', HOURS_TABLE,
        '<h2 id="contact">Find us</h2>',
        table([('Address', ADDRESS), ('Sales', SALES), ('Service', SERVICE),
               ('Parts', SERVICE), ('Region', 'Serving Edmonton, Sherwood Park, St. Albert and Leduc')]),
        '<p style="margin-top:18px"><a class="btn btn-red" href="{}" target="_blank" rel="noopener">'
        'Open in Google Maps</a></p>'.format(MAPS),
    ])

def service_page():
    return page('service', 'Service &amp; Parts', 'Keep your vehicle in factory condition',
                'Service & Parts', [
        '<p>Our service drive is open six days a week, and the Express Lane takes oil changes, '
        'inspections and quick maintenance without an appointment. Longer jobs get a loaner.</p>',
        cards2([('Express Lane', 'Oil changes, filters, wipers, batteries and multi-point '
                                 'inspections. No appointment &mdash; first come, first served.'),
                ('Scheduled maintenance', 'Factory-interval servicing that keeps your powertrain '
                                          'warranty intact, recorded against your VIN.'),
                ('Genuine Mopar parts', 'Ordered direct from the manufacturer, usually in hand '
                                        'within 24 hours. Fitted here or over the counter.'),
                ('Tire finder', 'Winter and all-season packages sized to your vehicle, with '
                                'seasonal storage available on site.'),
                ('Accessories', 'Lift kits, racks, running boards, tonneau covers and Jeep '
                                'Performance Parts, installed by our technicians.'),
                ('Collision centre', 'In-house body and paint, with insurance claims handled '
                                     'end to end.')]),
        '<h2>Service &amp; parts hours</h2>',
        table([h for h in HOURS if h[0] != 'Sales']),
        '<h2>Book a visit</h2>',
        '<p>Call the service desk at <a href="tel:{s}" style="color:#C30130;font-weight:700">{s}</a> '
        'or drop in at {a}.</p>'.format(s=SERVICE, a=ADDRESS),
    ])

def financing_page():
    rates = table([('72 months &mdash; new', '6.49% APR'), ('84 months &mdash; new', '6.99% APR'),
                   ('60 months &mdash; pre-owned', '7.49% APR'),
                   ('84 months &mdash; pre-owned', '8.29% APR'),
                   ('Manufacturer subvented (select trims)', 'from 3.99% APR')])
    return page('financing', 'Financing', 'Flexible terms for every credit situation', 'Financing', [
        '<p>We work with a dozen lenders, from the manufacturer&rsquo;s own finance arm through to '
        'specialists in rebuilding credit. Most applications come back the same day.</p>',
        cards2([('Apply online', 'A short application reviewed by our finance team, usually '
                                 'answered within a few hours on a business day.'),
                ('All credit situations', 'First-time buyers, new to Canada, bankruptcy discharge '
                                          'and rebuilding credit are all handled here.'),
                ('Value your trade', 'Bring your vehicle in for an appraisal and we will apply the '
                                     'value directly against your next one.'),
                ('Sell us your vehicle', 'We buy outright. No purchase required, and we handle the '
                                         'lien payout if there is one.')]),
        '<h2>Indicative rates</h2>', rates,
        '<p style="font-size:12px;color:#6b6b6b">Rates shown are examples for layout purposes and '
        'depend on term, credit and the vehicle financed.</p>',
        '<h2>Talk to the finance desk</h2>',
        '<p>Call <a href="tel:{s}" style="color:#C30130;font-weight:700">{s}</a> or ask for finance '
        'when you visit {a}.</p>'.format(s=SALES, a=ADDRESS),
    ])

def offers_page():
    return page('offers', 'Current offers', 'Manufacturer incentives and dealer promotions', 'Offers', [
        '<p>Employee Pricing is on across the eligible new lineup &mdash; the same price our own '
        'staff pay, shown on every qualifying vehicle in our new inventory.</p>',
        cards2([('Employee Pricing', 'Pay what we pay on eligible new Chrysler, Dodge, Jeep and Ram '
                                     'models. The discount is already applied to the prices you see.'),
                ('Finance rates from 3.99%', 'Manufacturer-subvented rates on selected trims, '
                                             'stackable with most cash incentives.'),
                ('Winter tires included', 'A winter tire and wheel package included on selected '
                                          'Jeep models while stock lasts.'),
                ('Service specials', 'Seasonal pricing on oil changes, brakes, batteries and '
                                     'alignment through the service drive.')]),
        '<h2>How the pricing reads</h2>',
        '<p>On every new listing the crossed-out figure is the retail price and the large figure is '
        'your price after the discount. The vehicle detail page breaks the two apart line by line.</p>',
        '<p style="margin-top:22px">'
        '<a class="btn btn-red" href="../new/inventory/search.html">Shop eligible new vehicles</a>'
        '<a class="btn btn-out" href="clearance.html" style="margin-left:8px">See clearance</a></p>',
    ])

# ---------------------------------------------------------------- filtered listing pages
def listing_page(slug, title, sub, active, rows, blurb):
    root = '../'
    sorts = ''.join('<option value="{}">{}</option>'.format(v, t) for v, t in SORTS)
    body = '''<div class="crumbs"><div class="wrap">
<a href="{r}index.html">Home</a> &rsaquo; {t}
</div></div>
<div class="wrap"><div class="srp">
{facets}
<div class="srp-main">
  <div class="srp-bar">
    <h1>{t} <span class="count">(<span id="resultCount">{n}</span>)</span></h1>
    <div class="srp-tools">
      <label for="sortOrder">Sort</label>
      <select id="sortOrder">{sorts}</select>
      <span class="viewtog"><button class="on" data-view="grid" type="button">&#9638; Grid</button><button data-view="list" type="button">&#9776; List</button></span>
    </div>
  </div>
  <div id="activeFilters" class="chips" hidden></div>
  <div id="compareBar" class="cmpbar" hidden></div>
  <p style="margin:-8px 0 18px;color:#6b6b6b;font-size:13px;max-width:720px">{blurb}</p>
  <p id="noResults" class="noresults" hidden>No vehicles match these filters.
     <button type="button" id="clearFilters2">Clear all filters</button></p>
  <div class="vgrid g3" id="results">
{cards}
  </div>
</div>
</div></div>
<script>window.FACET_MAP={facetmap};</script>
'''.format(r=root, t=title, n=len(rows), sorts=sorts, blurb=e(blurb),
           facets=facets_html(rows), cards='\n'.join(card(v, root) for v in rows),
           facetmap=json.dumps(FACET_MAP))
    ctx = page_context('content', page_name=slug, filters={}, result_count=len(rows), compare=[])
    return write('pages/{}.html'.format(slug), head(title, root, active, sub, ctx) + body + foot(root))

def clearance_page():
    rows = sorted([v for v in INV['new'] if v['was']],
                  key=lambda v: price_num(v['was']) - v['pricenum'], reverse=True)
    return listing_page('clearance', 'Clearance', 'Outgoing stock, priced to move', 'Clearance',
                        rows, 'Every new vehicle currently carrying a discount, biggest saving '
                              'first. Prices already reflect the reduction.')

def electric_page():
    rows = [v for v in ALL
            if v['fuel'] == 'Electric' or '4xe' in v['trim'] or 'Hybrid' in v['trim']]
    return listing_page('electric', 'Electric &amp; Hybrid', 'Plug-in 4xe and full electric models',
                        'Electric', rows,
                        'Jeep 4xe plug-in hybrids, the all-electric Recon and Charger Daytona, and '
                        'hybrid Pacifica models currently in stock.')

# ---------------------------------------------------------------- build
# ---------------------------------------------------------------- inventory export
# One flat JSON file in the Optimy inventory-table shape (see README).
EXPORT_STATUS = {'new': 'new', 'used': 'used', 'demos': 'demo'}
DEALER_CITY   = 'Edmonton'

def inventory_export():
    """Every vehicle on the site, one record per car, in listing order.
    page_num is 0-based and car_index 1-based within that status's listing
    (all cars sit on one listing page). Missing text -> "", missing number -> null."""
    out = []
    for cond in ('new', 'used', 'demos'):
        for i, v in enumerate(INV[cond], 1):
            out.append({
                'page_num': 0,
                'car_index': i,
                'image': v.get('img') or '',
                'status': EXPORT_STATUS[cond],
                'price': float(v['pricenum']) if v['pricenum'] else None,
                'make': v.get('make') or '',
                'model': v.get('model') or '',
                'year': float(v['year']) if str(v.get('year') or '').isdigit() else None,
                'trim': v['trimbase'],
                'mileage': float(v['kmnum']) if v['kmnum'] else None,
                'color': v['ext'],
                'city': DEALER_CITY,
                'stock_id': v.get('stock') or '',
                'vin': v.get('vin') or '',
            })
    with open(os.path.join(OUT, 'inventory.json'), 'w') as fh:
        json.dump(out, fh, indent=4)
    return out

if __name__ == '__main__':
    made = [home()]
    for c in SRP:
        made.append(srp(c))
    for v in ALL:
        made.append(vdp(v))
    made += [about_page(), service_page(), financing_page(), offers_page(),
             clearance_page(), electric_page()]
    exported = inventory_export()
    print('generated {} pages'.format(len(made)))
    print('  export  : inventory.json ({} vehicles)'.format(len(exported)))
    print('  home    : index.html')
    print('  search  : ' + ', '.join(SRP[c]['path'] for c in SRP))
    print('  vdp     : {} vehicle pages under new/inventory/, used/, demos/'.format(len(ALL)))
    print('  content : about, service, financing, offers, clearance, electric')
