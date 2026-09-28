# -*- coding: utf-8 -*-
"""Add mock listings for the models the live first page doesn't render,
using the real manufacturer profile images so the demo shows the full lineup."""
import json, re

inv = json.load(open('inventory.json'))
imgs = [l.strip() for l in open('carimgs.txt') if l.strip()]

# model -> (category, trim options, msrp, discount, engine, drive, doors, cyl, fuel)
SPECS = {
 'Wrangler':      ('SUV',   ['Sport S 4-Door','Rubicon 4xe','Sahara 4xe'],      48995,  4200, '3.6L Pentastar VVT V6 w/ESS',          'Four-wheel drive','4','6','Gas'),
 'Gladiator':     ('Truck', ['Sport S','Rubicon','Mojave'],                     57995,  5100, '3.6L Pentastar VVT V6 w/ESS',          'Four-wheel drive','4','6','Gas'),
 'Recon':         ('SUV',   ['Moab 4xe','Launch Edition'],                      66995,  3800, 'Dual eBeam electric drive modules',    'Four-wheel drive','4','0','Electric'),
 '1500':          ('Truck', ['Big Horn Crew Cab','Laramie Crew Cab','Rebel'],   54995,  6400, '3.0L Hurricane Straight-Six Turbo',    'Four-wheel drive','4','6','Gas'),
 '2500':          ('Truck', ['Big Horn Crew Cab','Laramie Mega Cab'],           72995,  7200, '6.7L Cummins Turbo Diesel I-6',        'Four-wheel drive','4','6','Diesel'),
 '3500':          ('Truck', ['Limited Longhorn Dually','Big Horn Crew Cab'],    78995,  8100, '6.7L Cummins High-Output Turbo Diesel','Four-wheel drive','4','6','Diesel'),
 'Durango':       ('SUV',   ['GT Plus AWD','R/T Plus AWD','SRT Hellcat'],       58995,  5600, '5.7L HEMI VVT V8 w/FuelSaver MDS',     'All-wheel drive', '4','8','Gas'),
 'Charger':       ('Cars',  ['Daytona R/T','Daytona Scat Pack','SIXPACK H.O.'], 61995,  5900, '400V 100 kWh dual-motor electric',      'All-wheel drive', '2','0','Electric'),
 'Pacifica':      ('Minivans',['Touring-L AWD','Pinnacle Hybrid','Limited AWD'],59995,  5300, '3.6L Pentastar VVT V6 w/ESS',          'All-wheel drive', '4','6','Gas'),
}
COLOURS = [('White','Black'),('Diamond Black','Black'),('Silver Zynith','Grey'),
           ('Firecracker Red','Black'),('Hydro Blue','Black'),('Bright White','Sea Salt')]
TRIMLINE = ['Heated Seats | Remote Start','Trailer Tow Group | Backup Camera',
            'Sun and Sound Group | GPS Navigation','Cold Weather Group | Forward Collision Warning',
            'Technology Group | Adaptive Cruise']

have = {(v['make'], v['model']) for v in inv['new']}
added = []
for n, url in enumerate(imgs):
    m = re.search(r'newcarimages/([^/]+)/([^/]+)/(\d{4})/', url)
    if not m:
        continue
    make, model, year = m.group(1), m.group(2), m.group(3)
    make = 'RAM' if make == 'Ram' else make
    if model not in SPECS or (make, model) in have:
        continue
    cat, trims, msrp, disc, eng, drive, doors, cyl, fuel = SPECS[model]
    trim  = trims[n % len(trims)]
    ext, ins = COLOURS[n % len(COLOURS)]
    msrp += (n % 4) * 1500
    price = msrp - disc
    vid   = str(9900000 + n)
    added.append(dict(
        id=vid, make=make, model=model, year=year,
        trim='{} | {}'.format(trim, TRIMLINE[n % len(TRIMLINE)]),
        stock='{}{}{}-NEW'.format(year[-2:], make[:2].upper(), 1000 + n * 7),
        vin='MOCK{}{}{}{}'.format(make[:2].upper(), year, model[:3].upper(), 100000 + n * 137)[:17],
        img=url, url='/new/inventory/{}-{}-{}-id{}.html'.format(year, make, model, vid),
        price='{:,}'.format(price), was='{:,}'.format(msrp),
        badge='Reduced Price' if n % 3 else '',
        desc='{} KM. Auto., Ext: {}, Int: {}'.format(10 + n * 3, ext, ins),
        spec={'Stock #': '', 'Engine': eng, 'Cylinders': cyl, 'Transmission': 'Auto.',
              'Drive train': drive, 'Fuel': fuel, 'Category': cat,
              'Exterior Colour': ext, 'Interior Colour': ins, 'Doors': doors},
        breakdown=[['Retail Price', '{:,}'.format(msrp)],
                   ['Employee Discount', '-{:,}'.format(disc)]]))

inv['new'] = inv['new'] + added
for v in added:
    v['spec']['Stock #'] = v['stock']
json.dump(inv, open('inventory.json', 'w'), indent=1)
print('added {} listings: {}'.format(
    len(added), ', '.join(sorted({'{} {}'.format(v['make'], v['model']) for v in added}))))
print('new total:', len(inv['new']))
