# Builds skills.html + item-*.html from the JSON inside route.html,
# rewrites the nav on every page and reworks the home hero.
import re, json, sys, os, glob
from html import escape as E

R = sys.argv[1]
os.chdir(R)
UPDATED = '24.11.2026'
route = open('route.html', encoding='utf-8').read()
D = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', route, re.S).group(1))
LAD = D['lad']
LEVELS = ['מתחיל', 'מתפתח', 'מיומן', 'מוביל']
STAGES = [('גן–ב׳', 1), ('ג׳–ו׳', 2), ('ז׳–ט׳', 2), ('י׳–י״ב', 3)]
CATSTY = {
    'S': '--fam:#2E9FD8;--fam-d:#17648C;--fam-l:#E6F4FB',
    'V': '--fam:#F08A3C;--fam-d:#A44E14;--fam-l:#FDF0E6',
    'C': '--fam:#7B6FD0;--fam-d:#4B3FA0;--fam-l:#EFEDFA',
}
CATSHORT = {'S': 'מיומנויות', 'V': 'ערכים', 'C': 'כשירויות משלימות'}

def fn(sid): return 'item-%s.html' % sid.lower()
def unit(s): return 'רכיבים' if ('ערך' in s['t'] or s['cat'] == 'V') else 'יכולות'

ITEMS = []
for c in D['cats']:
    for g in c['gr']:
        for s in g['sk']:
            s['cat'] = c['id']; s['grp'] = g['n']; ITEMS.append(s)
assert len(ITEMS) == 52, len(ITEMS)

# ---------- shell ----------
base = open('all-skills.html', encoding='utf-8').read()
HEAD_TAIL = base[base.index('<link rel="icon"'):base.index('</head>')]
header = base[base.index('<body'):base.index('<main id="main">')]
header = header[header.index('>') + 1:]
footer = base[base.index('</main>') + len('</main>'):]

NAV = [('skills.html', 'כל המיומנויות'), ('index.html', 'דף הבית'), ('route.html', 'מחשב המסלול'),
       ('activities.html', 'פעילויות לכיתה'), ('rubric.html', 'המדרג המלא'), ('workshop.html', 'סדנה ומשאבים')]
def nav_html(cur):
    return '<nav class="wrap main-nav" aria-label="ניווט ראשי"><ul>' + ''.join(
        '<li><a href="%s"%s>%s</a></li>' % (h, ' aria-current="page"' if h == cur else '', t) for h, t in NAV) + '</ul></nav>'
NAV_RE = re.compile(r'<nav class="wrap main-nav" aria-label="ניווט ראשי">.*?</nav>', re.S)

FOOT_NOTE = ('<p class="muted">ההגדרות והפירוק ליכולות לקוחים מהמקורות הרשמיים, כפי שרוכזו ב<a href="https://ramishaked.github.io/ed-skills/" target="_blank" rel="noopener">מפת המיומנויות והערכים</a> של המו"פ העירוני בחולון. '
             'הרמות, המעברים והיעדים לפי שלב חינוך הם הצעה של מרכז הל"ה למיומנויות, ואינם ניסוח של משרד החינוך. '
             'המתודולוגיה מבוססת על "למידה מבוססת מיומנויות: ארגז כלים למורה ולמנהל/ת", מרכז פואנטה, 2021.</p>')

def fix_footer(f):
    f = re.sub(r'<p class="muted">שש מיומנויות הליבה נבחרו.*?</p>', FOOT_NOTE, f, flags=re.S)
    f = f.replace('<strong>מרכז המיומנויות – הבוגרת והבוגר 2030</strong>', '<strong>מרכז הל"ה למיומנויות</strong>')
    f = re.sub(r'עודכן לאחרונה: [0-9.]+', 'עודכן לאחרונה: ' + UPDATED, f)
    return f

def page(name, title, desc, body, bodycls='core-page'):
    h = NAV_RE.sub(nav_html(name), header)
    out = ('<!doctype html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           '<title>%s</title>\n<meta name="description" content="%s">\n'
           '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n%s</head>\n'
           '<body class="%s">\n%s<main id="main">\n%s\n</main>%s') % (
        E(title), E(desc), E(title), E(desc), HEAD_TAIL, bodycls, h, body, fix_footer(footer))
    open(name, 'w', encoding='utf-8').write(out)

NOTE = ('<p class="core-draft"><b>חשוב לדעת:</b> ההגדרה והפירוק ל%s לקוחים מהמקורות הרשמיים. '
        'ארבע הרמות, "איך עוברים" והיעד לפי שלב חינוך הם הצעה של מרכז הל"ה למיומנויות, ונועדו להערכה מעצבת ולשיח, לא לציונים.</p>')

def src_line(s):
    if not s.get('src'): return ''
    parts = []
    for x in s['src']:
        t = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(x['l']), E(x['n']))) if x.get('l') else E(x['n'])
        if x.get('o'): t += ' (%s)' % E(x['o'])
        parts.append(t)
    return '<p class="src">מקור: %s</p>' % ' · '.join(parts)

# ---------- item pages ----------
for idx, s in enumerate(ITEMS):
    sty = CATSTY[s['cat']]
    u = unit(s)
    toc = ''.join('<li><a href="#%s"><span class="code">%s</span> %s</a></li>' % (a['id'], a['id'], E(a['n'])) for a in s['ab'])
    tgt_rows = ''.join('<tr><th scope="row">%s</th><td>%s</td></tr>' % (st, LEVELS[t]) for st, t in STAGES)
    abs_html = ''
    for a in s['ab']:
        track = ''
        for i, lv in enumerate(a['lv']):
            badges = ''.join('<span class="tgt">יעד ל%s</span>' % st for st, t in STAGES if t == i)
            track += '<li class="lv lv%d"><p class="lv-name">%d. %s</p><p class="lv-text">%s</p>%s</li>' % (i + 1, i + 1, LEVELS[i], E(lv), ('<p class="tgts">%s</p>' % badges) if badges else '')
            if i < 3:
                track += '<li class="tr"><span class="tr-lab">איך עוברים ל%s</span><span>%s</span></li>' % (LEVELS[i + 1], E(a['tr'][i]))
        lad = ''; acts = []
        for lid in a.get('lad', []):
            L = LAD.get(lid)
            if not L: continue
            lad += '<li><a href="rubric.html#%s"><span class="code">%s</span> %s</a></li>' % (lid, lid, E(L['title']))
            for x in L.get('acts', []):
                if x['h'] not in [y['h'] for y in acts]: acts.append(x)
        extra = ''
        if lad:
            extra += '<details class="from-rubric"><summary>מהמדרג של המרכז: %d תת-מיומנויות עם כלים</summary><ul class="sub-list">%s</ul></details>' % (len(a['lad']), lad)
        if acts:
            extra += '<details class="from-rubric"><summary>פעילויות מוכנות (%d)</summary><ul class="sub-list">%s</ul></details>' % (
                len(acts), ''.join('<li><a href="%s">%s <span class="muted">· %s</span></a></li>' % (E(x['h']), E(x['t']), E(x.get('info', ''))) for x in acts))
        meta = []
        if a.get('g'): meta.append(E(a['g']))
        if a.get('s20'): meta.append('חלק מ"הלומד העצמאי"')
        abs_html += ('<article class="ab" id="%s"><header class="ab-head"><span class="code">%s</span><h3>%s</h3></header>%s'
                     '<p class="def">%s</p><ol class="lv-track" aria-label="ארבע רמות ואיך עוברים ביניהן">%s</ol>%s'
                     '<p class="ab-links"><a class="btn" href="route.html#%s">פתיחה במחשב המסלול</a>%s</p></article>') % (
            a['id'], a['id'], E(a['n']), ('<p class="ab-meta">%s</p>' % ' · '.join(meta)) if meta else '', E(a['d']), track, extra,
            a['id'], (' <a class="ab-src" href="%s" target="_blank" rel="noopener">המקור הרשמי%s</a>' % (E(a['l']), (', עמ\' ' + E(a['p'])) if a.get('p') else '')) if a.get('l') else '')
    prev = ITEMS[idx - 1] if idx else None
    nxt = ITEMS[idx + 1] if idx + 1 < len(ITEMS) else None
    pn = '<nav class="wrap pn" aria-label="מעבר בין פריטים">%s%s</nav>' % (
        ('<a href="%s">→ %s</a>' % (fn(prev['id']), E(prev['n']))) if prev else '<span></span>',
        ('<a href="%s">%s ←</a>' % (fn(nxt['id']), E(nxt['n']))) if nxt else '<span></span>')
    body = (
        '<section class="fam-hero" style="%s"><div class="wrap"><p class="crumbs"><a href="skills.html">כל המיומנויות</a> › <a href="skills.html#%s">%s</a> › %s</p>'
        '<p class="eyebrow">%s · <span class="code">%s</span></p><h1>%s</h1><p class="lead">%s</p>%s</div></section>'
        '<div style="%s"><section class="wrap block item-top"><div class="item-intro">%s<h2>%d %s</h2><ol class="toc-list">%s</ol>'
        '<p><a class="btn ghost" href="route.html#%s">לבניית מסלול במחשב המסלול</a></p></div>'
        '<aside class="kd tgt-box"><h2>יעד מוצע לפי שלב חינוך</h2><table class="tgt-table"><tbody>%s</tbody></table>'
        '<p class="muted small">אותו יעד לכל ה%s. מתאימים לתלמידים שלכם.</p></aside></section>'
        '<section class="wrap block"><h2>ה%s: ארבע רמות ואיך עוברים</h2><div class="ab-list">%s</div></section>%s</div>'
    ) % (sty, s['cat'], CATSHORT[s['cat']], E(s['grp']), E(s['t']), s['id'], E(s['n']), E(s['d']), src_line(s),
         sty, NOTE % u, len(s['ab']), u, toc, s['id'], tgt_rows, u, u, abs_html, pn)
    page(fn(s['id']), '%s | מרכז הל"ה למיומנויות' % s['n'],
         '%s: הגדרה, %d %s, ארבע רמות ואיך עוברים מרמה לרמה.' % (s['n'], len(s['ab']), u), body)

# ---------- hub ----------
def card(s):
    d = s['d']
    short = d if len(d) <= 150 else d[:d.rfind(' ', 0, 150)] + '…'
    return ('<li class="it" data-t="%s"><a class="core-card" href="%s" style="%s"><span class="code">%s</span><b>%s</b><span>%s</span>'
            '<span class="count">%d %s</span></a></li>') % (
        E(' '.join([s['n'], s['d'], s['grp']] + [a['n'] for a in s['ab']])), fn(s['id']), CATSTY[s['cat']], s['id'], E(s['n']), E(short), len(s['ab']), unit(s))

gates = ''; secs = ''
for c in D['cats']:
    n = sum(len(g['sk']) for g in c['gr']); na = sum(len(s['ab']) for g in c['gr'] for s in g['sk'])
    gates += '<li><a class="core-card gate" href="#%s" style="%s"><b>%s</b><span>%s</span><span class="count">%d פריטים · %d %s</span></a></li>' % (
        c['id'], CATSTY[c['id']], E(c['n']), E(c['sub']), n, na, 'רכיבים' if c['id'] == 'V' else 'יכולות ורכיבים' if c['id'] == 'C' else 'יכולות')
    grs = ''
    for g in c['gr']:
        gd = ('<p class="muted">%s</p>' % E(g['d'])) if g.get('d') and c['id'] == 'S' else ''
        grs += '<div class="grp"><h3>%s <small>%d</small></h3>%s<ul class="core-grid">%s</ul></div>' % (E(g['n']), len(g['sk']), gd, ''.join(card(s) for s in g['sk']))
    secs += '<section class="wrap block gate-sec" id="%s" style="%s"><h2>%s <small>%d</small></h2><p>%s</p>%s</section>' % (
        c['id'], CATSTY[c['id']], E(c['n']), n, E(c['sub']), grs)

s20 = D['s20']
hub = (
    '<section class="hero hero2"><div class="wrap"><p class="eyebrow">מרכז הל"ה למיומנויות · פסג"ה חולון · תשפ"ז</p>'
    '<h1>כל המיומנויות<span>52 מיומנויות, ערכים וכשירויות, ו-200 יכולות</span></h1>'
    '<p class="lead">כל הפריטים שבמפת המיומנויות והערכים של המו"פ העירוני, בשלושה שערים. לכל פריט: הגדרה ומקור, פירוק ליכולות, ולכל יכולת ארבע רמות (מתחיל, מתפתח, מיומן, מוביל), איך עוברים מרמה לרמה ויעד מוצע לפי שלב חינוך.</p>'
    '<div class="cta"><a class="btn" href="#S">למיומנויות</a><a class="btn ghost" href="route.html">מחשב המסלול</a></div></div></section>'
    '<section class="wrap block"><ul class="core-grid gates">%s</ul>'
    '<div class="find"><label for="q">חיפוש מיומנות, ערך או יכולת</label><input id="q" type="search" placeholder="למשל: הקשבה, ויסות, מקורות מידע" autocomplete="off"><p id="qn" class="muted" aria-live="polite"></p></div>'
    '<p class="core-draft"><b>חשוב לדעת:</b> ההגדרות והפירוק לקוחים מהמקורות הרשמיים, כפי שרוכזו ב<a href="https://ramishaked.github.io/ed-skills/" target="_blank" rel="noopener">מפת המיומנויות והערכים</a>. הרמות, המעברים והיעדים הם הצעה של מרכז הל"ה למיומנויות.</p></section>'
    '%s'
    '<section class="wrap block"><div class="kd"><h2>%s</h2><p>%s</p><p class="muted">ביכולות שמסומנות "חלק מהלומד העצמאי" יש את התגית הזו גם בעמוד הפריט.</p></div></section>'
    '<script>(function(){var q=document.getElementById("q"),n=document.getElementById("qn"),its=[].slice.call(document.querySelectorAll(".it")),grps=[].slice.call(document.querySelectorAll(".grp")),secs=[].slice.call(document.querySelectorAll(".gate-sec"));'
    'function f(){var w=q.value.trim().split(/\\s+/).filter(Boolean),k=0;its.forEach(function(i){var ok=w.every(function(x){return i.dataset.t.indexOf(x)>-1;});i.hidden=!ok;if(ok)k++;});'
    'grps.forEach(function(g){g.hidden=!g.querySelector(".it:not([hidden])");});secs.forEach(function(s){s.hidden=!s.querySelector(".it:not([hidden])");});n.textContent=w.length?(k?k+" פריטים נמצאו":"לא נמצא. נסו מילה אחרת."):"";}'
    'q.addEventListener("input",f);})();</script>'
) % (gates, secs, E(s20['n']), E(s20['d']))
page('skills.html', 'כל המיומנויות | מרכז הל"ה למיומנויות',
     'כל 52 המיומנויות, הערכים והכשירויות המשלימות, עם 200 יכולות, ארבע רמות לכל יכולת ואיך עוברים מרמה לרמה.', hub)

# ---------- nav on all other pages ----------
for f in glob.glob('*.html'):
    if f.startswith(('print-', 'item-', 'wall')) or f in ('skills.html', 'route.html'): continue
    t = open(f, encoding='utf-8').read()
    if not NAV_RE.search(t): continue
    t2 = NAV_RE.sub(nav_html(f), t)
    if t2 != t: open(f, 'w', encoding='utf-8').write(t2)

# ---------- home hero + gates ----------
h = open('index.html', encoding='utf-8').read()
new_hero = (
    '<section class="hero hero2">\n <div class="wrap">\n  <p class="eyebrow">מרכז הל"ה למיומנויות · פסג"ה חולון · תשפ"ז</p>\n'
    '  <h1>מרכז הל"ה למיומנויות<span>הוראה, למידה, הערכה: כל המיומנויות, ברמות ובצעדים</span></h1>\n'
    '  <p class="lead">כל המיומנויות, הערכים והכשירויות המשלימות שבמפת המיומנויות העירונית, עם ארבע רמות לכל יכולת ואיך עוברים מרמה לרמה. לצידן: מיומנויות הליבה של חולון, מדרג מעמיק ופעילויות לכיתה.</p>\n'
    '  <div class="cta"><a class="btn" href="skills.html">לכל המיומנויות</a><a class="btn ghost" href="route.html">מחשב המסלול</a></div>\n </div>\n</section>\n'
    '<section class="wrap block" id="gates" aria-labelledby="gates-h">\n <h2 id="gates-h">שלושה שערים</h2>\n <ul class="core-grid gates">%s</ul>\n</section>\n') % gates.replace('href="#', 'href="skills.html#')
h = re.sub(r'<section class="hero hero2">.*?</section>\n(<section class="wrap block" id="gates".*?</section>\n)?', lambda m: new_hero, h, count=1, flags=re.S)
h = h.replace('<h2 id="core-h">מיומנויות הליבה</h2>', '<h2 id="core-h">מיומנויות הליבה של חולון</h2>')
h = re.sub(r'<title>.*?</title>', '<title>מרכז הל"ה למיומנויות | פסג"ה חולון</title>', h)
open('index.html', 'w', encoding='utf-8').write(h)

# ---------- css ----------
CSS_MARK = '/* === all-skills (gen_all) === */'
css = open('styles.css', encoding='utf-8').read()
if CSS_MARK in css: css = css[:css.index(CSS_MARK)]
css += CSS_MARK + '''
.gates .core-card b{font-size:1.45rem}
.find{margin:1.2rem 0;display:flex;flex-direction:column;gap:.35rem;max-width:36rem}
.find label{font-weight:700;color:var(--navy)}
.find input{font:inherit;padding:.6rem .9rem;border:1px solid var(--line);border-radius:10px}
.find input:focus{outline:3px solid #2E9FD8;outline-offset:1px}
.gate-sec>h2{border-bottom:4px solid var(--fam);padding-bottom:.3rem}
.gate-sec h2 small,.grp h3 small{font-family:Assistant,sans-serif;font-size:.85rem;color:var(--fam-d);background:var(--fam-l);border-radius:999px;padding:.05rem .6rem;vertical-align:middle}
.grp{margin-top:1.4rem} .grp h3{margin:0 0 .3rem;color:var(--navy)}
.core-card .code{align-self:flex-start}
.item-top{display:grid;grid-template-columns:minmax(0,1fr) 20rem;gap:1.5rem;align-items:start}
.toc-list{padding-inline-start:1.2rem} .toc-list a{text-decoration:none;color:var(--ink)} .toc-list a:hover{color:var(--fam-d)}
.tgt-table{border-collapse:collapse;width:100%}
.tgt-table th,.tgt-table td{text-align:start;padding:.4rem .5rem;border-top:1px solid var(--line)}
.tgt-table td{font-weight:700;color:var(--fam-d)}
.small{font-size:.88rem}
.ab-list{display:flex;flex-direction:column;gap:1.3rem}
.ab{border:1px solid var(--line);border-inline-start:6px solid var(--fam);border-radius:var(--radius);padding:1.2rem 1.4rem;background:#fff;scroll-margin-top:140px}
.ab-head{display:flex;gap:.6rem;align-items:baseline;flex-wrap:wrap} .ab-head h3{margin:0;color:var(--navy)}
.ab-meta{margin:.2rem 0 0;color:var(--muted);font-size:.9rem}
.lv-track{list-style:none;padding:0;margin:1rem 0;display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;gap:.5rem;align-items:stretch}
.lv{background:var(--bg);border-top:4px solid var(--fam);border-radius:10px;padding:.7rem .8rem}
.lv1{border-top-color:#cfd0dc}.lv2{border-top-color:color-mix(in srgb,var(--fam) 45%,#fff)}.lv3{border-top-color:color-mix(in srgb,var(--fam) 75%,#fff)}.lv4{background:var(--fam-l)}
.lv p{margin:0} .lv-name{font-weight:700;color:var(--fam-d);font-size:.92rem} .lv-text{font-size:.95rem;margin-top:.25rem!important}
.tgts{margin-top:.4rem!important;display:flex;flex-wrap:wrap;gap:.25rem}
.tgt{font-size:.75rem;font-weight:700;background:var(--fam-d);color:#fff;border-radius:999px;padding:.05rem .5rem}
.tr{display:flex;flex-direction:column;justify-content:center;gap:.2rem;max-width:9rem;font-size:.84rem;color:var(--muted);padding:.2rem 0}
.tr-lab{font-weight:700;color:var(--navy);font-size:.78rem}
.tr-lab::before{content:"← ";color:var(--fam)}
.ab-links{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;margin:.8rem 0 0}
.ab-src{font-size:.9rem;color:var(--fam-d)}
.from-rubric{margin-top:.5rem}
@media (max-width:980px){.lv-track{grid-template-columns:1fr}.tr{max-width:none;flex-direction:row;gap:.5rem;padding:.1rem .8rem;align-items:baseline}.tr-lab::before{content:"↓ "}}
@media (max-width:820px){.item-top{grid-template-columns:1fr}}
@media print{.ab{break-inside:avoid}.lv-track{grid-template-columns:1fr auto 1fr auto 1fr auto 1fr}.find,.ab-links .btn{display:none}}
'''
open('styles.css', 'w', encoding='utf-8').write(css)
print('ok', len(ITEMS), 'items')

# ---------- center name in header ----------
for f in glob.glob('*.html'):
    t = open(f, encoding='utf-8').read()
    t2 = t.replace('מרכז המיומנויות<small>הבוגרת והבוגר 2030</small>', 'מרכז הל"ה למיומנויות<small>הוראה · למידה · הערכה</small>')
    if t2 != t: open(f, 'w', encoding='utf-8').write(t2)
