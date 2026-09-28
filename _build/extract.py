import re,json,html as H

def txt(s):
    s=re.sub(r'<[^>]+>',' ',s)
    s=H.unescape(s)
    return re.sub(r'\s+',' ',s).strip()

def grab(card,pat,g=1,d=''):
    m=re.search(pat,card,re.S)
    return txt(m.group(g)) if m else d

def cards(fn):
    h=open(fn,encoding='utf-8',errors='ignore').read()
    parts=re.split(r'<li class="carBoxWrapper"',h)[1:]
    out=[]
    for c in parts:
        c=c[:c.find('</li>')+5] if '</li>' in c else c
        vid=grab(c,r'data-carid="(\d+)"')
        if not vid: continue
        img=grab(c,r'data-imgsrc="([^"]+)"')
        if not img: img=grab(c,r'<img[^>]+src="(https://imagescdn[^"]+)"')
        make=grab(c,r'data-make="([^"]*)"')
        model=grab(c,r'data-model="([^"]*)"')
        year=grab(c,r'data-year="([^"]*)"')
        stock=grab(c,r'data-(?:nostock|stock-number)="([^"]*)"')
        vin=grab(c,r'data-vin="([^"]*)"')
        trim=grab(c,r"<span class='divTrim'>(.*?)</span>").strip(' |')
        url=grab(c,r'href="(/[^"]*?id\d+\.html)"')
        price=grab(c,r"<span[^>]*class='dollarsigned p-base[^']*'[^>]*>([\d,]+)</span>")
        was=grab(c,r"class='dollarsigned p-final ttNormal'>([\d,]+)</span>")
        if not price:
            price=grab(c,r"class='dollarsigned[^']*'[^>]*>([\d,]+)</span>")
        badge=grab(c,r'<div class="carBanner[^"]*"[^>]*>\s*<div>\s*<span class="fa[^"]*"></span>\s*<span>(.*?)</span>')
        desc=grab(c,r"<span class='s-desc'>(.*?)</span>\s*<span id=\"info-btn")
        if not desc: desc=grab(c,r"<span class='s-desc'>(.*?)</span></span>")
        spec={}
        for k,v in re.findall(r'<span>\s*([A-Za-z #:][^<]*?):\s*</span>\s*<span class="-ph --s">\s*(.*?)\s*</span>',c,re.S):
            spec[txt(k).rstrip(':').strip()]=txt(v)
        bd=[]
        for lbl,amt in re.findall(r"<div>([^<]+)</div><div class='item-amt'>\s*<span class=\"format-price\">([-\d,]+)</span></div>",c):
            bd.append([txt(lbl),txt(amt)])
        out.append(dict(id=vid,make=make,model=model,year=year,trim=trim,stock=stock,vin=vin,
                        img=img,url=url,price=price,was=was,badge=badge,desc=desc,spec=spec,breakdown=bd))
    return out

def facets(fn):
    h=open(fn,encoding='utf-8',errors='ignore').read()
    out=[]
    for m in re.finditer(r'<div class="fltBox[^"]*" id="(flt\w+)">(.*?)<!-- CLOSE FILTER',h,re.S):
        fid,blk=m.group(1),m.group(2)
        title=grab(blk,r'<span class="divSpan">(.*?)</span>')
        opts=[]
        for om in re.finditer(r'<span class="lblTitle">(.*?)</span>.*?<span class="lblCount">\(?(\d+)\)?</span>',blk,re.S):
            opts.append([txt(om.group(1)),om.group(2)])
        if not opts:
            for om in re.finditer(r'<label[^>]*>(.*?)</label>',blk,re.S):
                t=txt(om.group(1))
                if t: opts.append([t,''])
        if title: out.append(dict(id=fid,title=title,options=opts[:14]))
    return out

data={}
for key,fn in [('new','new.html'),('demos','demos.html'),('used','used.html')]:
    cs=cards(fn)
    data[key]=cs
    print(key,len(cs),'cards')
    if cs: print('  sample:',json.dumps(cs[0],ensure_ascii=False)[:400])
json.dump(data,open('inventory.json','w'),indent=1)
f=facets('new.html')
json.dump(f,open('facets.json','w'),indent=1)
print('\nFACETS:',[(x['title'],len(x['options'])) for x in f])
