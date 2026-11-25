# Builds the "all skills" layer of the site from the JSON inside route.html and the
# activity files in data/. Safe to run again: every change it makes is regenerated.
#
#   python3 scripts/gen_site.py .
#
# What it does:
#   skills.html, item-*.html          hub + one page per item (52)
#   print-item-*.html                 assessment kit per item (self-assessment + observation grid)
#   activities.html                   adds the new activities, core-skill badges and filters
#   print-ACT-253.. .html             teacher sheet for every new activity
#   route.html                        adds the new activities to the route calculator data
#   index.html                        home page
#   nav + footer on every page
import re, json, sys, os, glob, importlib.util
from html import escape as E

R = sys.argv[1]
os.chdir(R)
UPDATED = '24.11.2026'
LEVELS = ['מתחיל', 'מתפתח', 'מיומן', 'מוביל']
STAGES = [('גן–ב׳', 1), ('ג׳–ו׳', 2), ('ז׳–ט׳', 2), ('י׳–י״ב', 3)]
CATSTY = {
    'S': '--fam:#2E9FD8;--fam-d:#17648C;--fam-l:#E6F4FB',
    'V': '--fam:#F08A3C;--fam-d:#A44E14;--fam-l:#FDF0E6',
    'C': '--fam:#7B6FD0;--fam-d:#4B3FA0;--fam-l:#EFEDFA',
}
CATSHORT = {'S': 'מיומנויות', 'V': 'ערכים', 'C': 'כשירויות משלימות'}
# Holon core skills, in the order the municipality listed them.
CORE = ['S11', 'C52', 'S10']
CORESTY = {
    'S11': '--fam:#E8432E;--fam-d:#A3271A;--fam-l:#FDEBE8',
    'C52': '--fam:#4E9F35;--fam-d:#2F6B1C;--fam-l:#EEF7E9',
    'S10': '--fam:#2E9FD8;--fam-d:#17648C;--fam-l:#E6F4FB',
}
FIRST_NEW_ACT = 253

route = open('route.html', encoding='utf-8').read()
DM = re.search(r'(<script type="application/json" id="data">)(.*?)(</script>)', route, re.S)
D = json.loads(DM.group(2))
LAD = D['lad']

def fn(sid): return 'item-%s.html' % sid.lower()
def kitfn(sid): return 'print-item-%s.html' % sid.lower()
def unit(s): return 'רכיבים' if ('ערך' in s['t'] or s['cat'] == 'V') else 'יכולות'
def trans(st): return 'משלב %d (%s) לשלב %d (%s)' % (st, LEVELS[st - 1], st + 1, LEVELS[st])

ITEMS, AB = [], {}
for c in D['cats']:
    for g in c['gr']:
        for s in g['sk']:
            s['cat'] = c['id']; s['grp'] = g['n']; ITEMS.append(s)
            for a in s['ab']:
                a['item'] = s; AB[a['id']] = a
SK = {s['id']: s for s in ITEMS}
assert len(ITEMS) == 52, len(ITEMS)

# ---------- new activities ----------
def load(path):
    spec = importlib.util.spec_from_file_location('m', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.ACTS
XA = []
for f in ['data/acts_core.py', 'data/acts_extra_1.py', 'data/acts_extra_2.py', 'data/acts_extra_3.py', 'data/acts_extra_4.py']:
    XA += load(f)
order = {a['id']: i for i, a in enumerate(AB.values())}
for x in XA: assert x['ab'] in AB, x['ab']
XA.sort(key=lambda x: (order[x['ab']], x['st']))
for i, x in enumerate(XA):
    x['id'] = 'ACT-%d' % (FIRST_NEW_ACT + i)
    x['item'] = AB[x['ab']]['item']['id']
XBY = {}
for x in XA: XBY.setdefault(x['ab'], []).append(x)

def lad_acts(a):
    out = []
    for l in a.get('lad', []):
        for y in LAD.get(l, {}).get('acts', []):
            if y['h'] not in [z['h'] for z in out]: out.append(y)
    return out

# coverage: every ability has at least one activity
missing = [a['id'] for a in AB.values() if not lad_acts(a) and not XBY.get(a['id'])]
assert not missing, missing

# which core item an existing activity serves
ACT_CORE = {}
for a in AB.values():
    if a['item']['id'] in CORE:
        for y in lad_acts(a):
            ACT_CORE.setdefault(y['h'].split('#')[1], a['item']['id'])

# ---------- shell ----------
base = open('skills.html' if os.path.exists('skills.html') else 'all-skills.html', encoding='utf-8').read()
HEAD_TAIL = base[base.index('<link rel="icon"'):base.index('</head>')]
header = base[base.index('<body'):base.index('<main id="main">')]
header = header[header.index('>') + 1:]
NAV = [('index.html', 'דף הבית'), ('skills.html', 'כל המיומנויות'), ('route.html', 'מחשב המסלול'),
       ('activities.html', 'פעילויות לכיתה'), ('rubric.html', 'המדרג המלא'), ('workshop.html', 'סדנה ומשאבים'), ('contact.html', 'כתבו לנו')]
def nav_html(cur):
    return '<nav class="wrap main-nav" aria-label="ניווט ראשי"><ul>' + ''.join(
        '<li><a href="%s"%s>%s</a></li>' % (h, ' aria-current="page"' if h == cur else '', t) for h, t in NAV) + '</ul></nav>'
NAV_RE = re.compile(r'<nav class="wrap main-nav" aria-label="ניווט ראשי">.*?</nav>', re.S)
FOOTER = '''<footer class="site-footer">
 <div class="wrap">
  <img src="assets/logo-vertical.png" alt="פסג&quot;ה חולון – מרכז הל&quot;ה למיומנויות" width="90" height="83">
  <p><strong>מרכז הל"ה למיומנויות</strong> · פסג"ה חולון · חקר. חדשנות. חברה.</p>
  <p class="muted">ההגדרות והפירוק ליכולות לקוחים מהמקורות הרשמיים, כפי שרוכזו ב<a href="https://ramishaked.github.io/ed-skills/" target="_blank" rel="noopener">מפת המיומנויות והערכים</a> של המו"פ העירוני בחולון. הרמות, המעברים והיעדים לפי שלב חינוך הם הצעה של מרכז הל"ה למיומנויות, ואינם ניסוח של משרד החינוך. המתודולוגיה מבוססת על "למידה מבוססת מיומנויות: ארגז כלים למורה ולמנהל/ת", מרכז פואנטה, 2021.</p>
  <p class="muted footer-contact" id="about">פסג&quot;ה חולון · שדרות ירושלים 101, חולון · טלפון: <a href="tel:+97237444703" dir="ltr">03-7444703</a> · וואטסאפ: <a href="https://wa.me/972553072407" target="_blank" rel="noopener" dir="ltr">055-3072407</a> · דוא&quot;ל: <a href="mailto:Secretary@pisga.org" dir="ltr">Secretary@pisga.org</a></p>
  <p class="muted updated">עודכן לאחרונה: %s</p>
 </div>
</footer>''' % UPDATED
FOOTER_PLAIN = FOOTER
ASK = ('<section class="ask-strip" aria-labelledby="ask-h"><div class="wrap ask-in"><div><h2 id="ask-h">אנחנו כאן לרשותכם</h2>'
       '<p>צריכים משהו להוראה יעילה ולא מצאתם? פעילות, כלי הערכה, ליווי לצוות או רעיון לשיעור: כתבו לנו ונחזור אליכם.</p></div>'
       '<a class="btn" href="contact.html">כתבו לנו</a></div></section>\n')
FOOTER = ASK + FOOTER_PLAIN
FOOT_RE = re.compile(r'(?:<section class="ask-strip".*?</section>\n)?<footer class="site-footer">.*?</footer>', re.S)
TAIL = '\n<script src="script.js"></script>\n</body>\n</html>\n'

def page(name, title, desc, body, bodycls='core-page', foot=None):
    h = NAV_RE.sub(nav_html(name), header)
    out = ('<!doctype html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           '<title>%s</title>\n<meta name="description" content="%s">\n'
           '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n%s</head>\n'
           '<body class="%s">\n%s<main id="main">\n%s\n</main>\n%s%s') % (
        E(title), E(desc), E(title), E(desc), HEAD_TAIL, bodycls, h, body, foot or FOOTER, TAIL)
    open(name, 'w', encoding='utf-8').write(out)

def src_line(s):
    if not s.get('src'): return ''
    parts = []
    for x in s['src']:
        t = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(x['l']), E(x['n']))) if x.get('l') else E(x['n'])
        if x.get('o'): t += ' (%s)' % E(x['o'])
        parts.append(t)
    return '<p class="src">מקור: %s</p>' % ' · '.join(parts)

NOTE = ('<p class="core-draft"><b>חשוב לדעת:</b> ההגדרה והפירוק ל%s לקוחים מהמקורות הרשמיים. '
        'ארבע הרמות, "איך עוברים" והיעד לפי שלב חינוך הם הצעה של מרכז הל"ה למיומנויות, ונועדו להערכה מעצבת ולשיח, לא לציונים.</p>')

def item_sty(s): return CORESTY.get(s['id'], CATSTY[s['cat']])
def n_acts(s): return len({y['h'] for a in s['ab'] for y in lad_acts(a)} | {x['id'] for a in s['ab'] for x in XBY.get(a['id'], [])})

# ---------- item pages ----------
for idx, s in enumerate(ITEMS):
    sty = item_sty(s); u = unit(s); is_core = s['id'] in CORE
    toc = ''.join('<li><a href="#%s"><span class="code">%s</span> %s</a></li>' % (a['id'], a['id'], E(a['n'])) for a in s['ab'])
    tgt_rows = ''.join('<tr><th scope="row">%s</th><td>%s</td></tr>' % (st, LEVELS[t]) for st, t in STAGES)
    abs_html = ''
    for a in s['ab']:
        xs = XBY.get(a['id'], [])
        track = ''
        for i, lv in enumerate(a['lv']):
            badges = ''.join('<span class="tgt">יעד ל%s</span>' % st for st, t in STAGES if t == i)
            track += '<li class="lv lv%d"><p class="lv-name">%d. %s</p><p class="lv-text">%s</p>%s</li>' % (i + 1, i + 1, LEVELS[i], E(lv), ('<p class="tgts">%s</p>' % badges) if badges else '')
            if i < 3:
                tx = [x for x in xs if x['st'] == i + 1]
                act = ''.join('<a class="tr-act" href="activities.html#%s">פעילות: %s</a>' % (x['id'], E(x['n'])) for x in tx)
                track += '<li class="tr"><span class="tr-lab">איך עוברים ל%s</span><span>%s</span>%s</li>' % (LEVELS[i + 1], E(a['tr'][i]), act)
        lad = ''.join('<li><a href="rubric.html#%s"><span class="code">%s</span> %s</a></li>' % (lid, lid, E(LAD[lid]['title'])) for lid in a.get('lad', []) if lid in LAD)
        la = lad_acts(a)
        rows = [('activities.html#' + x['id'], x['n'], '%d דק\' · %s' % (x['dur'], trans(x['st']))) for x in xs] + [(y['h'], y['t'], y.get('info', '')) for y in la]
        extra = ''
        if rows:
            extra += '<details class="from-rubric"%s><summary>פעילויות לכיתה (%d)</summary><ul class="sub-list">%s</ul></details>' % (
                ' open' if is_core else '', len(rows), ''.join('<li><a href="%s">%s <span class="muted">· %s</span></a></li>' % (E(h), E(t), E(i)) for h, t, i in rows))
        if lad:
            extra += '<details class="from-rubric"><summary>מהמדרג של המרכז: %d תת-מיומנויות עם כלים</summary><ul class="sub-list">%s</ul></details>' % (len(a['lad']), lad)
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
    core_flag = '<p class="core-flag">מיומנות ליבה של חולון</p>' if is_core else ''
    kit = ('<div class="kit-box"><h2>כלי הערכה להדפסה</h2><p>כרטיס הערכה עצמית לתלמיד, בניסוח "אני...", וטבלת תצפית למורה לכל ה%s.</p>'
           '<p><a class="btn" href="%s">לכלי ההערכה ←</a></p></div>') % (u, kitfn(s['id']))
    core_intro = ''
    if is_core:
        core_intro = ('<section class="wrap block core-how"><h2>איך עובדים עם מיומנות ליבה</h2><ol class="steps">'
                      '<li><b>מאבחנים</b> עם כרטיס ההערכה העצמית וטבלת התצפית: באיזו רמה רוב הכיתה בכל %s?</li>'
                      '<li><b>בוחרים מעבר</b> אחד: לכל מעבר בין רמות יש כאן פעילות מוכנה, מסומנת בסולם.</li>'
                      '<li><b>מתרגלים</b> את הפעילות כמה פעמים, בכמה מקצועות, לאורך כמה שבועות.</li>'
                      '<li><b>חוזרים לאבחון</b> ומתעדים בשפת הרמות: מתחיל, מתפתח, מיומן, מוביל.</li></ol></section>') % ('יכולת' if u == 'יכולות' else 'רכיב')
    body = (
        '<section class="fam-hero" style="%s"><div class="wrap"><p class="crumbs"><a href="skills.html">כל המיומנויות</a> › <a href="skills.html#%s">%s</a> › %s</p>'
        '%s<p class="eyebrow">%s · <span class="code">%s</span></p><h1>%s</h1><p class="lead">%s</p>%s</div></section>'
        '<div style="%s"><section class="wrap block item-top"><div class="item-intro">%s<h2>%d %s</h2><ol class="toc-list">%s</ol>'
        '<p class="cta-row"><a class="btn ghost" href="route.html#%s">לבניית מסלול במחשב המסלול</a></p></div>'
        '<aside class="side"><div class="kd tgt-box"><h2>יעד מוצע לפי שלב חינוך</h2><table class="tgt-table"><tbody>%s</tbody></table>'
        '<p class="muted small">אותו יעד לכל ה%s. מתאימים לתלמידים שלכם.</p></div>%s</aside></section>%s'
        '<section class="wrap block"><h2>ה%s: ארבע רמות ואיך עוברים</h2><div class="ab-list">%s</div></section>%s</div>'
    ) % (sty, s['cat'], CATSHORT[s['cat']], E(s['grp']), core_flag, E(s['t']), s['id'], E(s['n']), E(s['d']), src_line(s),
         sty, NOTE % u, len(s['ab']), u, toc, s['id'], tgt_rows, u, kit, core_intro, u, abs_html, pn)
    body += ('<section class="wrap block"><p class="ask-inline">חסר לכם משהו ב%s? <a href="contact.html?item=%s">כתבו לנו מה צריך</a> ונחזור אליכם.</p></section>' % (E(s['n']), s['id']))
    page(fn(s['id']), '%s | מרכז הל"ה למיומנויות' % s['n'],
         '%s: הגדרה, %d %s, ארבע רמות, איך עוברים מרמה לרמה ופעילויות לכיתה.' % (s['n'], len(s['ab']), u), body)

# ---------- print kits ----------
KIT_CSS = ('<style>.sa-ab{margin:0 0 4mm;break-inside:avoid}.sa-ab h2{margin:0 0 1.5mm;font-size:12pt}.sa-ab ol{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(4,1fr);gap:2mm}'
           '.sa-ab li{border:1px solid #c9cad8;border-radius:2mm;padding:2mm;font-size:9.5pt;display:flex;flex-direction:column;gap:1mm}.sa-ab li b{font-size:8.5pt;color:#29275E}'
           '.sa-ab li i{display:block;width:5mm;height:5mm;border:1.5px solid #29275E;border-radius:50%%;margin-top:auto}'
           '.obs{border-collapse:collapse;width:100%%;font-size:9pt}.obs th,.obs td{border:1px solid #9a9bb0;padding:1.2mm 1.5mm;text-align:start}.obs td{height:6.2mm}.obs thead th{background:#29275E;color:#fff;font-weight:600}'
           '.legend{font-size:9pt;margin:2mm 0}.line{border-bottom:1px solid #9a9bb0;height:7mm}</style>')
def kit_head(title, back):
    return ('<!doctype html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s – להדפסה | מרכז הל"ה למיומנויות</title>\n<link rel="icon" href="assets/logo-vertical.png">\n<link rel="stylesheet" href="print.css">\n%s</head>\n<body class="kit">\n'
            '<div class="toolbar"><a href="%s">→ חזרה</a><span class="t-title">%s</span><button type="button" class="print-now" onclick="pisgaPrint()">הדפסה</button></div>\n<main>\n') % (E(title), KIT_CSS, back, E(title))
def sheet(label, tag, title, inner, pill):
    return ('<section class="sheet" aria-label="%s">\n<div class="s-head"><span class="pill"><span>%s</span></span><img class="s-logo" src="assets/logo-horizontal.png" alt="פסג&quot;ה חולון"></div>\n'
            '<div class="tag">%s</div>\n<div class="s-title"><h1>%s</h1></div>\n%s\n<div class="s-foot"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span></div></section>\n') % (E(label), E(pill), tag, E(title), inner)
KIT_END = '</main>\n<script src="script.js"></script>\n</body>\n</html>\n'

for s in ITEMS:
    u = unit(s)
    sa = '<p class="intro">קוראים כל שורה ומסמנים את המשפט שהכי מתאר אותך היום. אין תשובה נכונה: זה עוזר לנו לבחור את הצעד הבא.</p>'
    sa += '<p class="legend">שם: ____________________ &nbsp; כיתה: ______ &nbsp; תאריך: __________</p>'
    for a in s['ab']:
        sa += '<div class="sa-ab"><h2>%s</h2><ol>%s</ol></div>' % (E(a['n']), ''.join('<li><b>%s</b>%s<i></i></li>' % (LEVELS[i], E(lv)) for i, lv in enumerate(a['lv'])))
    sa += '<p class="legend"><b>הצעד הבא שלי:</b></p><div class="line"></div>'
    heads = ''.join('<th scope="col">%s</th>' % E(a['n']) for a in s['ab'])
    obs = ('<p class="legend">כותבים בכל משבצת את הרמה שראיתם: 1 מתחיל · 2 מתפתח · 3 מיומן · 4 מוביל. אפשר להוסיף תאריך ותצפית קצרה.</p>'
           '<table class="obs"><thead><tr><th scope="col">שם התלמיד</th>%s</tr></thead><tbody>%s</tbody></table>') % (
        heads, ''.join('<tr><td></td>%s</tr>' % ''.join('<td></td>' for _ in s['ab']) for _ in range(24)))
    out = kit_head('כלי הערכה: ' + s['n'], fn(s['id']))
    out += sheet('הערכה עצמית', 'לתלמידים', 'איפה אני ב%s?' % s['n'], sa, s['n'])
    out += sheet('טבלת תצפית', 'למורה', 'טבלת תצפית: ' + s['n'], obs, s['n'])
    open(kitfn(s['id']), 'w', encoding='utf-8').write(out + KIT_END)

for x in XA:
    a = AB[x['ab']]; s = a['item']
    inner = ('<div class="meta"><div><b>משך</b>%d דקות</div><div><b>יכולת</b>%s</div><div><b>מעבר בין רמות</b>%s</div></div>'
             '<h2>חומרים</h2><p>%s</p><h2>מהלך</h2><ol class="steps">%s</ol><div class="box"><h2>שאלה לסיכום</h2><ul class="qs"><li>%s</li></ul></div>') % (
        x['dur'], E(a['n']), trans(x['st']), E(x['mat']), ''.join('<li>%s</li>' % E(t) for t in x['steps']), E(x['q']))
    two = []
    if x.get('look'): two.append('<div class="box"><h2>מה מחפשים</h2><p>%s</p></div>' % E(x['look']))
    if x.get('ad'): two.append('<div class="box"><h2>גרסה מותאמת</h2><p>%s</p></div>' % E(x['ad']))
    two.append('<div class="box"><h2>דוגמה מתחום דעת</h2><p>%s</p></div>' % E(x['ex']))
    inner += '<div class="two">%s</div>' % ''.join(two)
    out = kit_head(x['n'], 'activities.html#' + x['id']) + sheet(x['n'], 'למורה', x['n'], inner, s['n']) + KIT_END
    open('print-%s.html' % x['id'], 'w', encoding='utf-8').write(out)

# ---------- activities page ----------
A = open('activities.html', encoding='utf-8').read()
A = re.sub(r'<!--x-acts:start-->.*?<!--x-acts:end-->', '', A, flags=re.S)
A = re.sub(r'<!--x-toc:start-->.*?<!--x-toc:end-->', '', A, flags=re.S)
A = re.sub(r'<p class="core-badge"[^>]*>.*?</p>', '', A, flags=re.S)
def badge(cid):
    return '<p class="core-badge" style="%s"><a href="%s">מיומנות ליבה של חולון: %s</a></p>' % (CORESTY[cid], fn(cid), E(SK[cid]['n']))
def fix_art(m):
    tag, aid = m.group(1), m.group(2)
    core = ACT_CORE.get(aid)
    tag = re.sub(r' data-core="[^"]*"', '', tag).replace('<article ', '<article data-core="%s" ' % (core.lower() if core else 'none'), 1)
    return tag + m.group(3) + (badge(core) if core else '')
A = re.sub(r'(<article [^>]*id="(ACT-\d+)"[^>]*>)((?:<p class="crumbs">.*?</p>)?<h3>.*?</h3>)', fix_art, A)
core_opts = '<option value="">הכול</option>' + ''.join('<option value="%s">%s</option>' % (c.lower(), E(SK[c]['n'])) for c in CORE) + '<option value="none">מחוץ לליבה</option>'
A = re.sub(r'<label>[^<]*<select id="af-core">.*?</select></label>', '<label>מיומנות ליבה של חולון<select id="af-core">%s</select></label>' % core_opts, A, flags=re.S)
FAMS = [('core', 'מיומנויות הליבה של חולון'), ('emo', 'מודעות עצמית'), ('lit', 'אוריינות לשונית'), ('think', 'חשיבה ביקורתית'), ('other', 'שאר המיומנויות'), ('vals', 'ערכים'), ('comp', 'כשירויות משלימות')]
A = re.sub(r'<select id="af-fam">.*?</select>', '<select id="af-fam"><option value="">כל המשפחות</option>%s</select>' % ''.join('<option value="%s">%s</option>' % f for f in FAMS), A, flags=re.S)
def xfam(x):
    if x['item'] in CORE: return 'core', fn(x['item'])[:-5]
    c = SK[x['item']]['cat']
    if x['item'] == 'S01': return 'lit', 'item-s01'
    if c == 'S': return 'other', 'official-' + str(int(x['item'][1:]))
    return ('vals' if c == 'V' else 'comp'), fn(x['item'])[:-5]
skopts = re.search(r'<select id="af-skill">(.*?)</select>', A, re.S).group(1)
skopts = re.sub(r'<option value="item-[^"]*"[^>]*>[^<]*</option>', '', skopts)
newopts = ''.join('<option value="%s" data-fam="core">%s</option>' % (fn(c)[:-5], E(SK[c]['n'])) for c in CORE)
newopts += '<option value="item-s01" data-fam="lit">הערכת טקסט</option>'
for s in ITEMS:
    if s['cat'] in 'VC' and s['id'] not in CORE:
        newopts += '<option value="%s" data-fam="%s">%s</option>' % (fn(s['id'])[:-5], 'vals' if s['cat'] == 'V' else 'comp', E(s['n']))
A = re.sub(r'<select id="af-skill">.*?</select>', lambda m: '<select id="af-skill">%s%s</select>' % (skopts, newopts), A, flags=re.S)

def art(x):
    a = AB[x['ab']]; s = a['item']; fam, skill = xfam(x)
    core = x['item'] if x['item'] in CORE else None
    h = ('<article class="act fam-%s" id="%s" data-core="%s" data-fam="%s" data-skill="%s" data-stage="%d" data-dur="%d"><h3>%s</h3>%s'
         '<dl class="act-meta"><dt>משך</dt><dd>%d דקות</dd><dt>יכולת</dt><dd><a href="%s#%s">%s</a> · %s</dd><dt>מעבר</dt><dd>%s</dd></dl>'
         '<h4>חומרים</h4><p>%s</p><h4>מהלך</h4><ol class="act-steps">%s</ol><h4>שאלה לסיכום</h4><ul><li>%s</li></ul>') % (
        'x' if fam in ('other',) else fam, x['id'], core.lower() if core else 'none', fam, skill, x['st'], x['dur'], E(x['n']), badge(core) if core else '',
        x['dur'], fn(s['id']), a['id'], E(a['n']), E(s['n']), trans(x['st']), E(x['mat']), ''.join('<li>%s</li>' % E(t) for t in x['steps']), E(x['q']))
    if x.get('look'): h += '<h4>מה מחפשים</h4><p>%s</p>' % E(x['look'])
    if x.get('ad'): h += '<h4>גרסה מותאמת</h4><p>%s</p>' % E(x['ad'])
    h += '<h4>דוגמה מתחום דעת</h4><p>%s</p><p class="kit-link"><a class="btn" href="print-%s.html">דף למורה להדפסה ←</a></p></article>' % (E(x['ex']), x['id'])
    return h
groups = [('core', 'מיומנויות הליבה של חולון', [x for x in XA if x['item'] in CORE]),
          ('vals', 'ערכים', [x for x in XA if SK[x['item']]['cat'] == 'V']),
          ('comp', 'כשירויות משלימות', [x for x in XA if SK[x['item']]['cat'] == 'C' and x['item'] not in CORE]),
          ('x', 'השלמות: אוריינות לשונית ואוריינות גופנית-בריאותית', [x for x in XA if SK[x['item']]['cat'] == 'S' and x['item'] not in CORE])]
xhtml = '<!--x-acts:start-->'
for k, t, xs in groups:
    intro = ''
    if k == 'core':
        intro = '<p class="spec-link">פעילות לכל מעבר בין רמות בכל אחת מיכולות הליבה. לכל פעילות: מה מחפשים כדי לדעת שהתלמיד עלה רמה, וגרסה מותאמת.</p>'
    xhtml += '<h2 class="fam-h fam-%s">%s</h2>%s<div class="acts">%s</div>' % (k, t, intro, ''.join(art(x) for x in xs))
xhtml += '<!--x-acts:end-->'
end = A.rindex('</article></div></section>') + len('</article></div>')
A = A[:end] + xhtml + A[end:]
toc_end = A.index('</ul></nav>', A.index('<nav class="toc"'))
A = A[:toc_end] + '<!--x-toc:start-->' + ''.join('<li><a href="#%s">%s</a></li>' % (x['id'], E(x['n'])) for x in XA) + '<!--x-toc:end-->' + A[toc_end:]
A = A.replace('<div class="wrap backbar"><a class="back-wheel" href="all-skills.html#wheel">→ חזרה לגלגל המיומנויות</a></div>', '<div class="wrap backbar"><a class="back-wheel" href="skills.html">→ חזרה לכל המיומנויות</a></div>')
A = re.sub(r'פעילויות של 5–15 דקות בתוך שיעור רגיל\. כל פעילות מקדמת תת-מיומנות אחת משלב לשלב',
           'פעילויות של 5–15 דקות בתוך שיעור רגיל, לכל המיומנויות, הערכים והכשירויות. כל פעילות מקדמת יכולת אחת מרמה לרמה', A)
open('activities.html', 'w', encoding='utf-8').write(A)

# ---------- route calculator: add the new activities ----------
for a in AB.values():
    xs = XBY.get(a['id'], [])
    src = None
    for c in D['cats']:
        for g in c['gr']:
            for s in g['sk']:
                for b in s['ab']:
                    if b['id'] == a['id']: src = b
    if src is None: continue
    if xs: src['xa'] = [{'t': x['n'], 'h': 'activities.html#' + x['id'], 'info': '%d דק\', %s' % (x['dur'], trans(x['st']))} for x in xs]
    else: src.pop('xa', None)
for s in ITEMS:
    s.pop('cat', None); s.pop('grp', None)
    for a in s['ab']: a.pop('item', None)
route = route[:DM.start(2)] + json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + route[DM.end(2):]
if 'var xa = a.xa' not in route:
    route = route.replace("if (!ids.length && !sids.length) { c.hidden = true; return; }",
                          "var xa = a.xa || [];\n    if (!ids.length && !sids.length && !xa.length) { c.hidden = true; return; }")
    route = route.replace("    if (ids.length) {\n      c.appendChild(el('div', 'grp-h', 'ליכולת \"' + a.n + '\"'));",
        "    if (xa.length) {\n      var xb = el('div', 'acts'); xb.appendChild(el('b', null, 'פעילויות לכיתה ליכולת הזו:'));\n"
        "      xa.forEach(function (x) { var row = el('div'); var a1 = el('a', null, x.t); a1.href = BASE + x.h; a1.target = '_blank'; a1.rel = 'noopener'; row.appendChild(a1); row.appendChild(document.createTextNode(' (' + x.info + ') · ')); var a2 = el('a', null, 'דף להדפסה'); a2.href = BASE + 'print-' + x.h.split('#')[1] + '.html'; a2.target = '_blank'; a2.rel = 'noopener'; row.appendChild(a2); xb.appendChild(row); });\n"
        "      c.appendChild(xb);\n    }\n    if (ids.length) {\n      c.appendChild(el('div', 'grp-h', 'ליכולת \"' + a.n + '\"'));")
    assert 'xb.appendChild(row)' in route, 'route patch failed'
open('route.html', 'w', encoding='utf-8').write(route)
for s in ITEMS: s['cat'] = 'S' if s['id'][0] == 'S' else s['id'][0]

# ---------- hub ----------
for c in D['cats']:
    for g in c['gr']:
        for s in g['sk']: s['cat'] = c['id']; s['grp'] = g['n']
def card(s):
    d = s['d']; short = d if len(d) <= 150 else d[:d.rfind(' ', 0, 150)] + '…'
    flag = '<span class="core-tag">ליבה בחולון</span>' if s['id'] in CORE else ''
    return ('<li class="it" data-t="%s"><a class="core-card" href="%s" style="%s"><span class="code">%s</span>%s<b>%s</b><span>%s</span>'
            '<span class="count">%d %s · %d פעילויות</span></a></li>') % (
        E(' '.join([s['n'], s['d'], s['grp']] + [a['n'] for a in s['ab']])), fn(s['id']), item_sty(s), s['id'], flag, E(s['n']), E(short), len(s['ab']), unit(s), n_acts(s))
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
TOTAL_ACTS = 252 + len(XA)
hub = (
    '<section class="hero hero2"><div class="wrap"><p class="eyebrow">מרכז הל"ה למיומנויות · פסג"ה חולון · תשפ"ז</p>'
    '<h1>כל המיומנויות<span>52 מיומנויות, ערכים וכשירויות, 200 יכולות ו-%d פעילויות</span></h1>'
    '<p class="lead">כל הפריטים שבמפת המיומנויות והערכים של המו"פ העירוני, בשלושה שערים. לכל פריט: הגדרה ומקור, פירוק ליכולות, ולכל יכולת ארבע רמות (מתחיל, מתפתח, מיומן, מוביל), איך עוברים מרמה לרמה, יעד מוצע לפי שלב חינוך ופעילויות לכיתה.</p>'
    '<div class="cta"><a class="btn" href="#S">למיומנויות</a><a class="btn ghost" href="route.html">מחשב המסלול</a></div></div></section>'
    '<section class="wrap block"><ul class="core-grid gates">%s</ul>'
    '<div class="find"><label for="q">חיפוש מיומנות, ערך או יכולת</label><input id="q" type="search" placeholder="למשל: הקשבה, ויסות, מקורות מידע" autocomplete="off"><p id="qn" class="muted" aria-live="polite"></p></div>'
    '<p class="muted">פריטים שמסומנים "ליבה בחולון" הם מיומנויות הליבה שנבחרו בעירייה: %s.</p></section>'
    '%s'
    '<section class="wrap block"><div class="kd"><h2>%s</h2><p>%s</p><p class="muted">ביכולות שמסומנות "חלק מהלומד העצמאי" יש את התגית הזו גם בעמוד הפריט.</p></div></section>'
    '<script>(function(){var q=document.getElementById("q"),n=document.getElementById("qn"),its=[].slice.call(document.querySelectorAll(".it")),grps=[].slice.call(document.querySelectorAll(".grp")),secs=[].slice.call(document.querySelectorAll(".gate-sec"));'
    'function f(){var w=q.value.trim().split(/\\s+/).filter(Boolean),k=0;its.forEach(function(i){var ok=w.every(function(x){return i.dataset.t.indexOf(x)>-1;});i.hidden=!ok;if(ok)k++;});'
    'grps.forEach(function(g){g.hidden=!g.querySelector(".it:not([hidden])");});secs.forEach(function(s){s.hidden=!s.querySelector(".it:not([hidden])");});n.textContent=w.length?(k?k+" פריטים נמצאו":"לא נמצא. נסו מילה אחרת."):"";}'
    'q.addEventListener("input",f);})();</script>'
) % (TOTAL_ACTS, gates, ', '.join(E(SK[c]['n']) for c in CORE), secs, E(s20['n']), E(s20['d']))
page('skills.html', 'כל המיומנויות | מרכז הל"ה למיומנויות',
     'כל 52 המיומנויות, הערכים והכשירויות המשלימות, עם 200 יכולות, ארבע רמות לכל יכולת, איך עוברים מרמה לרמה ופעילויות לכיתה.', hub)

# ---------- contact page ----------
item_opts = ''.join('<option value="%s">%s</option>' % (E(s['n']), E(s['n'])) for s in ITEMS)
core_opts2 = ''.join('<option value="%s">%s (ליבה בחולון)</option>' % (E(SK[c]['n']), E(SK[c]['n'])) for c in CORE)
item_ids = json.dumps({s['id']: s['n'] for s in ITEMS}, ensure_ascii=False)
contact = '''<section class="fam-hero" style="--fam:#29275E;--fam-d:#29275E;--fam-l:#ECEBF5"><div class="wrap">
<p class="eyebrow">מרכז הל"ה למיומנויות</p><h1>כתבו לנו</h1>
<p class="lead">אנחנו כאן לרשותכם. צריכים משהו להוראה יעילה ולא מצאתם באתר? פעילות למיומנות מסוימת, כלי הערכה, ליווי לצוות או סדנה: ספרו לנו מה צריך ונחזור אליכם.</p></div></section>
<section class="wrap block contact-wrap">
<form id="cform" class="cform" novalidate>
 <div id="formView">
 <fieldset><legend>מה אתם צריכים?</legend>
  <label for="c-kind">סוג הפנייה</label>
  <select id="c-kind" name="kind"><option>חומר או פעילות להוראה</option><option>כלי הערכה</option><option>ליווי לצוות או סדנה</option><option>שאלה על האתר</option><option>הצעה או משוב</option><option>אחר</option></select>
  <label for="c-item">מיומנות, ערך או כשירות <span class="opt">(לא חובה)</span></label>
  <select id="c-item" name="item"><option value="">כללי, לא מיומנות מסוימת</option><optgroup label="מיומנויות הליבה של חולון">%s</optgroup><optgroup label="כל המיומנויות, הערכים והכשירויות">%s</optgroup></select>
  <label for="c-grade">שכבת גיל <span class="opt">(לא חובה)</span></label>
  <select id="c-grade" name="grade"><option value="">לא רלוונטי</option><option>גן–ב׳</option><option>ג׳–ו׳</option><option>ז׳–ט׳</option><option>י׳–י״ב</option><option>צוות מורים</option></select>
  <label for="c-msg">מה הייתם רוצים? <span class="req">*</span></label>
  <textarea id="c-msg" name="msg" rows="6" maxlength="2000" placeholder="למשל: פעילות קצרה לעבודת צוות בכיתה ז׳, שאפשר לשלב בשיעור מדעים"></textarea>
 </fieldset>
 <fieldset><legend>איך נחזור אליכם?</legend>
  <div class="row2">
   <div><label for="c-name">שם מלא <span class="req">*</span></label><input id="c-name" name="name" autocomplete="name" maxlength="80"></div>
   <div><label for="c-role">תפקיד</label><input id="c-role" name="role" maxlength="80" placeholder="מורה, רכזת, מנהל..."></div>
  </div>
  <label for="c-school">בית ספר או גן</label><input id="c-school" name="school" maxlength="120" autocomplete="organization">
  <div class="row2">
   <div><label for="c-email">דוא"ל</label><input id="c-email" name="email" type="email" autocomplete="email" dir="ltr" maxlength="120"></div>
   <div><label for="c-phone">טלפון</label><input id="c-phone" name="phone" type="tel" autocomplete="tel" dir="ltr" maxlength="30"></div>
  </div>
  <p class="opt">צריך לפחות דוא"ל או טלפון.</p>
  <label class="chk"><input id="c-ok" type="checkbox"> אני מסכים/ה שצוות מרכז הל"ה ייצור איתי קשר בעניין הפנייה <span class="req">*</span></label>
  <div class="hp" aria-hidden="true"><label for="c-web">אתר</label><input id="c-web" name="website" tabindex="-1" autocomplete="off"></div>
 </fieldset>
 <p id="c-err" class="c-err" role="alert" hidden></p>
 <button id="c-send" type="submit" class="btn">שליחה</button>
 </div>
 <div id="doneView" class="c-done" hidden><h2>תודה, הפנייה התקבלה</h2><p>נחזור אליכם בהקדם. אפשר להמשיך <a href="skills.html">לכל המיומנויות</a> או <a href="activities.html">לפעילויות לכיתה</a>.</p>
  <button id="c-again" type="button" class="btn ghost">פנייה נוספת</button></div>
 <div id="mailView" class="c-done" hidden><h2>נפתחה הודעת דוא"ל</h2><p>הפנייה הוכנה בתוכנת הדוא"ל שלכם, ונשאר ללחוץ "שלח". אם לא נפתח דבר, אפשר לכתוב ישירות ל<span id="c-addr" dir="ltr"></span>.</p></div>
</form>
<aside class="contact-side">
 <h2>אפשר גם כך</h2>
 <p>טלפון: <a href="tel:+97237444703" dir="ltr">03-7444703</a></p>
 <p>וואטסאפ: <a href="https://wa.me/972553072407" target="_blank" rel="noopener" dir="ltr">055-3072407</a></p>
 <p>דוא"ל: <a id="c-mail" href="mailto:Secretary@pisga.org" dir="ltr">Secretary@pisga.org</a></p>
 <p class="muted">פסג"ה חולון · שדרות ירושלים 101, חולון</p>
</aside>
</section>
<script src="contact-config.js"></script>
<script>
(function(){
var $=function(i){return document.getElementById(i);};
var ITEMS=%s;
var cfg=window.CONTACT||{};
if(cfg.email){$('c-mail').href='mailto:'+cfg.email;$('c-mail').textContent=cfg.email;}
try{var q=new URLSearchParams(location.search).get('item');if(q&&ITEMS[q]){$('c-item').value=ITEMS[q];}}catch(e){}
function v(i){return ($(i).value||'').trim();}
$('cform').addEventListener('submit',function(ev){
 ev.preventDefault();
 var err=$('c-err');err.hidden=true;
 var d={kind:v('c-kind'),item:v('c-item'),grade:v('c-grade'),msg:v('c-msg'),name:v('c-name'),role:v('c-role'),school:v('c-school'),email:v('c-email'),phone:v('c-phone'),website:v('c-web'),page:document.referrer||''};
 var miss=[];
 if(!d.msg)miss.push('מה הייתם רוצים');
 if(!d.name)miss.push('שם');
 if(!d.email&&!d.phone)miss.push('דוא"ל או טלפון');
 if(d.email&&!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(d.email))miss.push('דוא"ל תקין');
 if(!$('c-ok').checked)miss.push('הסכמה ליצירת קשר');
 if(miss.length){err.textContent='חסר: '+miss.join(', ');err.hidden=false;return;}
 var b=$('c-send');
 if(!cfg.api){
  var to=cfg.email||'Secretary@pisga.org';
  var body=['סוג הפנייה: '+d.kind,'מיומנות: '+(d.item||'כללי'),'שכבה: '+(d.grade||'-'),'','הפנייה:',d.msg,'','שם: '+d.name,'תפקיד: '+d.role,'בית ספר: '+d.school,'דוא"ל: '+d.email,'טלפון: '+d.phone].join('\\n');
  $('c-addr').textContent=to;
  location.href='mailto:'+to+'?subject='+encodeURIComponent('פנייה לאתר מרכז הל"ה: '+d.kind)+'&body='+encodeURIComponent(body);
  $('formView').hidden=true;$('mailView').hidden=false;return;
 }
 b.disabled=true;b.textContent='שולחים...';
 fetch(cfg.api,{method:'POST',body:JSON.stringify(d)}).then(function(r){return r.json();}).then(function(res){
  b.disabled=false;b.textContent='שליחה';
  if(!res||!res.ok)throw new Error(res&&res.error||'נסו שוב');
  $('formView').hidden=true;$('doneView').hidden=false;window.scrollTo(0,0);
 }).catch(function(e){b.disabled=false;b.textContent='שליחה';err.textContent='השליחה לא הצליחה ('+(e&&e.message?e.message:'נסו שוב')+'). אפשר גם להתקשר או לכתוב לנו בדוא"ל.';err.hidden=false;});
});
$('c-again').addEventListener('click',function(){$('cform').reset();$('doneView').hidden=true;$('formView').hidden=false;});
})();
</script>''' % (core_opts2, item_opts, item_ids)
page('contact.html', 'כתבו לנו | מרכז הל"ה למיומנויות',
     'צריכים משהו להוראה יעילה ולא מצאתם? כתבו לצוות מרכז הל"ה למיומנויות ונחזור אליכם.', contact, foot=FOOTER_PLAIN)
if not os.path.exists('contact-config.js'):
    open('contact-config.js', 'w', encoding='utf-8').write(
        "// טופס \"כתבו לנו\"\n"
        "// api: כתובת ה-exec של Apps Script בגיליון הפניות (פריסה כאפליקציית אינטרנט, גישה: כל אחד).\n"
        "//      כל עוד היא ריקה, הטופס פותח הודעת דוא\"ל מוכנה לכתובת שבשדה email.\n"
        "window.CONTACT = {\n  api: '',\n  email: 'Secretary@pisga.org'\n};\n")

# ---------- home ----------
old = open('index.html', encoding='utf-8').read()
m = re.search(r'<section class="wrap block escape-block">.*?</section>', old, re.S)
escape = m.group(0) if m else ''
core_cards = ''
for i, c in enumerate(CORE):
    s = SK[c]; d = s['d']; short = d if len(d) <= 170 else d[:d.rfind(' ', 0, 170)] + '…'
    nx = sum(len(XBY.get(a['id'], [])) for a in s['ab'])
    core_cards += ('<li><a class="core-card" href="%s" style="%s"><span class="core-num">%d</span><b>%s</b><span>%s</span>'
                   '<span class="core-abs">%s</span><span class="count">%d %s · %d פעילויות · כלי הערכה</span></a></li>') % (
        fn(c), CORESTY[c], i + 1, E(s['n']), E(short), ' · '.join(E(a['n']) for a in s['ab']), len(s['ab']), unit(s), n_acts(s))
home = (
    '<section class="hero hero2">\n <div class="wrap">\n  <p class="eyebrow">אתר מלווה למורים · פסג"ה חולון · תשפ"ז</p>\n'
    '  <h1>מרכז הל"ה למיומנויות<span>הוראה, למידה, הערכה: כל המיומנויות, ברמות ובפעילויות</span></h1>\n'
    '  <p class="lead">כל המיומנויות, הערכים והכשירויות שבמפת המיומנויות העירונית, עם ארבע רמות לכל יכולת, איך עוברים מרמה לרמה ופעילויות של 5–15 דקות לכל מעבר. במרכז: שלוש מיומנויות הליבה שנבחרו בחולון.</p>\n'
    '  <div class="cta"><a class="btn" href="#core">למיומנויות הליבה</a><a class="btn ghost" href="skills.html">לכל המיומנויות</a></div>\n </div>\n</section>\n'
    '<section class="wrap block" id="core" aria-labelledby="core-h">\n <h2 id="core-h">מיומנויות הליבה של חולון</h2>\n'
    ' <p>שלוש המיומנויות שנבחרו בעירייה. לכל אחת: פירוק ליכולות, ארבע רמות, פעילות מוכנה לכל מעבר בין רמות וכלי הערכה להדפסה.</p>\n'
    ' <ul class="core-grid core3">%s</ul>\n</section>\n'
    '<section class="wrap block" id="gates" aria-labelledby="gates-h">\n <h2 id="gates-h">כל המיומנויות, בשלושה שערים</h2>\n <ul class="core-grid gates">%s</ul>\n</section>\n'
    '<section class="wrap block">\n <h2>איך זה עובד</h2>\n <ul class="how4">'
    '<li><b>יכולות</b><span>כל מיומנות, ערך או כשירות מפורקים ליכולות, לפי המקורות הרשמיים.</span></li>'
    '<li><b>ארבע רמות</b><span>לכל יכולת: מתחיל, מתפתח, מיומן, מוביל, בניסוח של התלמיד: "אני...".</span></li>'
    '<li><b>איך עוברים</b><span>בין כל שתי רמות: מה עושים בכיתה, ופעילות מוכנה של 5–15 דקות.</span></li>'
    '<li><b>יעד לפי שלב</b><span>יעד מוצע לכל שלב חינוך, מגן ועד י״ב. מתאימים לתלמידים שלכם.</span></li></ul>\n</section>\n'
    '<section class="wrap block" id="start">\n <h2>מאיפה מתחילים</h2>\n <ol class="steps">'
    '<li><b>בוחרים יכולת</b> מתוך מיומנויות הליבה, או מתוך כל המיומנויות לפי מה שבית הספר בחר.</li>'
    '<li><b>מזהים רמה</b> עם כרטיס ההערכה העצמית וטבלת התצפית: באיזו רמה רוב הכיתה?</li>'
    '<li><b>בוחרים פעילות</b> שמקדמת לרמה הבאה, ומשלבים אותה בשיעור הקרוב.</li>'
    '<li><b>מתעדים בשפת הרמות</b> ומספרים לעמית מה קרה. <a href="route.html">מחשב המסלול</a> עוזר לבנות את הרצף.</li></ol>\n</section>\n'
    '%s\n'
) % (core_cards, gates.replace('href="#', 'href="skills.html#'), escape)
hb = old[:old.index('<main id="main">') + len('<main id="main">')] + '\n' + home + '</main>\n' + FOOTER + TAIL
hb = re.sub(r'<title>.*?</title>', '<title>מרכז הל"ה למיומנויות | פסג"ה חולון</title>', hb)
hb = re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*"', r'\1אתר מלווה למורים: כל המיומנויות, הערכים והכשירויות, ארבע רמות לכל יכולת, פעילויות לכיתה ושלוש מיומנויות הליבה של חולון."', hb)
hb = re.sub(r'<meta property="og:title"[^\n]*>', '<meta property="og:title" content="מרכז הל&quot;ה למיומנויות">', hb)
open('index.html', 'w', encoding='utf-8').write(hb)

# ---------- remove the old six-core pages ----------
for f in glob.glob('core-*.html') + ['steps.html']:
    if os.path.exists(f): os.remove(f)

# ---------- nav, footer and wording on every page ----------
for f in glob.glob('*.html'):
    if f.startswith(('print-', 'wall')) or f == 'route.html': continue
    t = open(f, encoding='utf-8').read(); t0 = t
    t = NAV_RE.sub(nav_html(f), t)
    t = FOOT_RE.sub(lambda m: FOOTER_PLAIN if f == 'contact.html' else FOOTER, t)
    t = t.replace('מרכז המיומנויות<small>הבוגרת והבוגר 2030</small>', 'מרכז הל"ה למיומנויות<small>הוראה · למידה · הערכה</small>')
    t = t.replace('זו המסגרת המלאה של משרד החינוך, שממנה נבחרו <a href="index.html#core">שש מיומנויות הליבה</a>.',
                  'זו המסגרת המלאה של משרד החינוך. <a href="skills.html">כל המיומנויות</a>, הערכים והכשירויות, עם רמות ופעילויות, נמצאים בעמוד נפרד.')
    t = re.sub(r'href="(core-[a-z]+|steps)\.html[^"]*"', 'href="index.html#core"', t)
    if t != t0: open(f, 'w', encoding='utf-8').write(t)

for f in glob.glob('print-*.html'):
    t = open(f, encoding='utf-8').read()
    t2 = re.sub(r'href="(core-[a-z]+|steps)\.html[^"]*"', 'href="index.html#core"', t)
    if t2 != t: open(f, 'w', encoding='utf-8').write(t2)

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
.core-tag{align-self:flex-start;font-size:.78rem;font-weight:700;background:var(--fam-d);color:#fff;border-radius:999px;padding:.05rem .6rem}
.core-flag{display:inline-block;margin:.3rem 0 0;font-size:.85rem;font-weight:700;background:var(--fam-d);color:#fff;border-radius:999px;padding:.1rem .8rem}
.core3 .core-card b{font-size:1.5rem}
.core-abs{font-size:.9rem;color:var(--fam-d);font-weight:600}
.how4{list-style:none;padding:0;margin:1rem 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem}
.how4 li{background:var(--bg);border-radius:var(--radius);padding:1rem 1.1rem;display:flex;flex-direction:column;gap:.3rem}
.how4 b{font-family:"Secular One",sans-serif;font-weight:400;font-size:1.2rem;color:var(--navy)}
.item-top{display:grid;grid-template-columns:minmax(0,1fr) 20rem;gap:1.5rem;align-items:start}
.side{display:flex;flex-direction:column;gap:1rem}
.kit-box{border:2px solid var(--fam);border-radius:var(--radius);padding:1rem 1.2rem;background:var(--fam-l)}
.kit-box h2{margin:0 0 .3rem;font-size:1.2rem} .kit-box p{margin:.3rem 0}
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
.tr{display:flex;flex-direction:column;justify-content:center;gap:.25rem;max-width:9.5rem;font-size:.84rem;color:var(--muted);padding:.2rem 0}
.tr-lab{font-weight:700;color:var(--navy);font-size:.78rem}
.tr-lab::before{content:"← ";color:var(--fam)}
.tr-act{display:inline-block;font-weight:700;font-size:.8rem;color:var(--fam-d);background:var(--fam-l);border:1px solid var(--fam);border-radius:8px;padding:.15rem .45rem;text-decoration:none}
.tr-act:hover{background:var(--fam);color:#fff}
.ab-links{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;margin:.8rem 0 0}
.ab-src{font-size:.9rem;color:var(--fam-d)}
.from-rubric{margin-top:.5rem}
.act.fam-core,.fam-h.fam-core{--fam:#E8432E;--fam-d:#A3271A;--fam-l:#FDEBE8}
.act.fam-vals,.fam-h.fam-vals{--fam:#F08A3C;--fam-d:#A44E14;--fam-l:#FDF0E6}
.act.fam-comp,.fam-h.fam-comp{--fam:#7B6FD0;--fam-d:#4B3FA0;--fam-l:#EFEDFA}
.ask-strip{background:#29275E;color:#fff;margin-top:2.5rem}
.ask-in{display:flex;align-items:center;justify-content:space-between;gap:1.5rem;flex-wrap:wrap;padding-block:1.6rem}
.ask-in h2{margin:0 0 .3rem;color:#fff;font-size:1.5rem}.ask-in p{margin:0;max-width:44rem;color:#E3E2F0}
.ask-strip .btn{background:#F08A3C;border-color:#F08A3C;color:#1D1C3A}.ask-strip .btn:hover{background:#fff;border-color:#fff}
.ask-inline{background:var(--bg);border-radius:var(--radius);padding:.9rem 1.2rem;margin:0}
.contact-wrap{display:grid;grid-template-columns:minmax(0,1fr) 18rem;gap:2rem;align-items:start}
.cform fieldset{border:1px solid var(--line);border-radius:var(--radius);padding:1rem 1.2rem 1.2rem;margin:0 0 1.2rem;display:flex;flex-direction:column;gap:.35rem}
.cform legend{font-family:"Secular One",sans-serif;font-size:1.2rem;color:var(--navy);padding:0 .4rem}
.cform label{font-weight:700;color:var(--navy);margin-top:.5rem}
.cform input,.cform select,.cform textarea{font:inherit;padding:.6rem .8rem;border:1px solid var(--line);border-radius:10px;background:#fff;width:100%;box-sizing:border-box}
.cform input:focus,.cform select:focus,.cform textarea:focus{outline:3px solid #2E9FD8;outline-offset:1px}
.cform .row2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.cform .chk{display:flex;gap:.5rem;align-items:flex-start;font-weight:400;color:var(--ink)}.cform .chk input{width:auto;margin-top:.3rem}
.opt{font-weight:400;color:var(--muted);font-size:.88rem;margin:0}.req{color:#C0392B}
.hp{position:absolute;inset-inline-start:-9999px;width:1px;height:1px;overflow:hidden}
.c-err{color:#A3271A;background:#FDEBE8;border-radius:10px;padding:.6rem .9rem;margin:0 0 1rem}
.c-done{background:#EEF7E9;border-radius:var(--radius);padding:1.2rem 1.4rem}
.contact-side{background:var(--bg);border-radius:var(--radius);padding:1.2rem 1.3rem}.contact-side h2{margin-top:0;font-size:1.25rem}
@media (max-width:820px){.contact-wrap{grid-template-columns:1fr}.cform .row2{grid-template-columns:1fr}}
.act.fam-lit{--fam:var(--orange);--fam-d:var(--orange-d);--fam-l:#fdf0e6}
@media (max-width:980px){.lv-track{grid-template-columns:1fr}.tr{max-width:none;padding:.1rem .8rem}.tr-lab::before{content:"↓ "}}
@media (max-width:820px){.item-top{grid-template-columns:1fr}}
@media print{.ab{break-inside:avoid}.lv-track{grid-template-columns:1fr auto 1fr auto 1fr auto 1fr}.find,.ab-links .btn,.kit-box .btn{display:none}}
'''
open('styles.css', 'w', encoding='utf-8').write(css)
print('ok: %d items, %d new activities (ACT-%d to ACT-%d), core: %s' % (len(ITEMS), len(XA), FIRST_NEW_ACT, FIRST_NEW_ACT + len(XA) - 1, ', '.join(CORE)))
