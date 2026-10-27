# -*- coding: utf-8 -*-
"""
Update Shutoko Chronicle.html with multilingual support, database,
clean data-driven changes, removal of start page, and universal seat succession.
"""

import os, sys, json, re, csv

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\scratch')

from build_chronicle_multilingual import build_multilingual_database, load_story_cutscenes, load_pa_dialogues, BASE_TR

GLOSSARY_FILES = [
    ('monikers', 'Monikers', 'master_monikers_i18n.csv'),
    ('teams', 'Teams', 'master_teams_i18n.csv'),
    ('persons', 'Persons', 'master_persons_i18n.csv'),
    ('lexicon', 'Lexicon', 'shutoko_battle_lexicon_i18n.csv'),
]

def load_glossary():
    out = []
    for gid, title, fname in GLOSSARY_FILES:
        path = os.path.join(BASE_TR, fname)
        if not os.path.exists(path):
            print('WARNING: glossary file missing:', path)
            continue
        with open(path, 'r', encoding='utf-8-sig', errors='ignore', newline='') as f:
            rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
        if rows:
            out.append({'id': gid, 'title': title, 'cols': rows[0], 'rows': rows[1:]})
    return out

# JP-only build: drop translated bios/relations/story text so only JP sources render.
# Set to False to bring translations back.
STRICT_JP = True

def strip_translations(db):
    for r in db.get('recs', []):
        r['text_en'] = ''
        r['rel'] = ''
        r['bio_i18n'] = {}
        r['rel_i18n'] = {}
    for t in db.get('teams', []):
        if 'bio_i18n' in t:
            t['bio_i18n'] = {}
    for lines in (db.get('story') or {}).values():
        for ln in lines:
            ln['i18n'] = {}
    for areas in (db.get('pa') or {}).values():
        for entries in areas.values():
            for e in entries:
                e['i18n'] = {}

GLOSSARY_JS = r"""
      var _setModeBase = setMode;
      setMode = function (m, keep) { if (m === 'glossary') return setGlossaryMode(); return _setModeBase(m, keep) };
      function setGlossaryMode() {
        state.mode = 'glossary'; state.sel = null; state.themes = {};
        document.querySelector('.layout').classList.remove('has-sel');
        document.querySelectorAll('.tab').forEach(function (t) { t.setAttribute('aria-selected', t.dataset.mode === 'glossary' ? 'true' : 'false') });
        document.getElementById('rail').hidden = true;
        document.querySelector('.layout').style.gridTemplateColumns = '1fr';
        var v = document.getElementById('view');
        var G2 = D.glossary || [];
        var h = '<p class="eyebrow">Reference</p><h2 class="title">Glossary</h2><p class="aka">Master translation tables used for names, bynames, teams and series terms.</p>';
        G2.forEach(function (g, gi) {
          h += '<details class="gl" data-gi="' + gi + '" style="margin:12px 0;border:1px solid rgba(128,128,128,.35);border-radius:6px;padding:8px 12px"><summary style="cursor:pointer;font-weight:600">' + esc(g.title) + ' <small class="dim">' + g.rows.length + ' entries</small></summary><div class="gl-body"></div></details>';
        });
        v.innerHTML = h;
        v.querySelectorAll('details.gl').forEach(function (d) {
          d.addEventListener('toggle', function () { if (d.open && !d.dataset.built) { d.dataset.built = '1'; buildGlossary(d, G2[+d.dataset.gi]) } });
        });
        window.scrollTo(0, 0);
      }
      function buildGlossary(d, g) {
        var body = d.querySelector('.gl-body');
        body.innerHTML = '<input type="search" placeholder="Filter" style="width:100%;margin:8px 0;padding:6px" aria-label="Filter ' + esc(g.title) + '"><div class="scroll" style="max-height:70vh;overflow:auto"></div>';
        var box = body.querySelector('.scroll'), inp = body.querySelector('input');
        function draw() {
          var q = inp.value.trim().toLowerCase(), n = 0;
          var t = '<table class="tg" style="width:100%;table-layout:auto"><thead><tr>' + g.cols.map(function (c) { return '<th style="text-align:left;position:sticky;top:0;background:var(--bg,#fff)">' + esc(c) + '</th>' }).join('') + '</tr></thead><tbody>';
          for (var i = 0; i < g.rows.length && n < 500; i++) {
            var r = g.rows[i];
            if (q && r.join(' ').toLowerCase().indexOf(q) < 0) continue;
            n++;
            t += '<tr>' + r.map(function (c) { return '<td style="vertical-align:top">' + esc(c) + '</td>' }).join('') + '</tr>';
          }
          box.innerHTML = t + '</tbody></table>' + (n >= 500 ? '<p class="dim">Showing first 500. Use the filter.</p>' : '');
        }
        inp.oninput = draw; draw();
      }
"""

STORY_UI_JS = r"""
      /* STORY_PA_UI */
      var STORY_GAMES = { SB0: 'Shutokou Battle 0', SB01: 'Shutokou Battle 01', SBX: 'Shutokou Battle X', SB2025: 'Shutokou Battle (2025)' };
      var SPK = null;
      function speakerIndex() {
        if (SPK) return SPK; SPK = {};
        D.persons.forEach(function (p) {
          var add = function (s) { var k = nk(String(s || '').replace(/[\u2606\u2605]/g, '')); if (k && !SPK[k]) SPK[k] = p.id };
          add(p.name); add(p.disp); add(p.nick); add(p.name_en);
          (p.recs || []).forEach(function (i) { var r = R[i]; add(r.disp); add(r.real); add(r.nick) });
        });
        return SPK;
      }
      function speakerHtml(ch, pid) {
        if (!ch) return '';
        var id = pid || speakerIndex()[nk(String(ch).replace(/[\u2606\u2605]/g, ''))];
        return id ? '<button type="button" class="linkbtn" data-p="' + id + '"><b>' + esc(ch) + '</b></button>' : '<b>' + esc(ch) + '</b>';
      }
      var PAIDX = null;
      function paIndex() {
        if (PAIDX) return PAIDX; PAIDX = {};
        var gi = {}; D.games.forEach(function (g, i) { gi[g.id] = i });
        var rc = {}; R.forEach(function (r) { rc[r.g + '|' + r.id] = r.pid });
        Object.keys(D.pa || {}).forEach(function (g) {
          Object.keys(D.pa[g]).forEach(function (area) {
            D.pa[g][area].forEach(function (e) {
              var pid = e.rcode ? rc[gi[g] + '|' + e.rcode] : speakerIndex()[nk(String(e.speaker || '').replace(/[\u2606\u2605]/g, ''))];
              e._pid = pid;
              if (pid) (PAIDX[pid] = PAIDX[pid] || []).push({ g: g, area: area, e: e });
            });
          });
        });
        return PAIDX;
      }
      function lineHtml(who, jp, i18n) {
        var L = curLang(), tr = (i18n && L !== 'JP') ? i18n[L] : '';
        return '<div style="margin:0 0 10px;padding-left:10px;border-left:2px solid var(--amber,#c90)">' + (who ? '<div>' + who + '</div>' : '') + '<div>' + esc(jp) + '</div>' + (tr ? '<div class="dim" style="margin-top:2px">' + esc(tr) + '</div>' : '') + '</div>';
      }
      function setStoryMode(m) {
        state.mode = m; state.sel = null; state.themes = {};
        document.querySelector('.layout').classList.remove('has-sel');
        document.querySelectorAll('.tab').forEach(function (t) { t.setAttribute('aria-selected', t.dataset.mode === m ? 'true' : 'false') });
        document.getElementById('rail').hidden = true;
        document.querySelector('.layout').style.gridTemplateColumns = '1fr';
        renderStory(m);
      }
      function renderStory(m) {
        var opts = (m === 'poems' ? ['SB0', 'SB01'] : ['SBX', 'SB2025']).filter(function (g) { return (D.story && D.story[g]) || (D.pa && D.pa[g]) });
        state.sg = state.sg || {};
        var g = state.sg[m] && opts.indexOf(state.sg[m]) >= 0 ? state.sg[m] : opts[0];
        var v = document.getElementById('view');
        var h = '<p class="eyebrow">' + (m === 'poems' ? 'Poems' : 'Story &amp; Parking Area') + '</p><h2 class="title">' + (m === 'poems' ? 'Poems' : 'Story &amp; Parking Area') + '</h2>';
        if (!g) { v.innerHTML = h + '<p class="dim">No data loaded.</p>'; return }
        h += '<div class="chips" style="margin:8px 0 14px">' + opts.map(function (o) { return '<button type="button" class="chip" data-sg="' + o + '" aria-pressed="' + (o === g) + '">' + esc(STORY_GAMES[o] || o) + '</button>' }).join('') + '</div>';
        var st = (D.story && D.story[g]) || [], last = '';
        if (st.length) h += '<h3 class="sec">Story</h3>';
        st.forEach(function (ln) {
          var key = [ln.stage, ln.sub, ln.heading].join('|');
          if (key !== last) { last = key; h += '<h4 style="margin:16px 0 6px">' + esc([ln.stage, ln.sub, ln.heading].filter(Boolean).join(' \u00b7 ')) + '</h4>' }
          h += lineHtml(speakerHtml(ln.char), ln.jp, ln.i18n);
        });
        var pa = (D.pa && D.pa[g]) || null;
        if (pa && m !== 'poems') {
          paIndex();
          h += '<h3 class="sec">Parking Area chat</h3>';
          Object.keys(pa).forEach(function (area) {
            h += '<h4 style="margin:16px 0 6px">' + esc(area) + '</h4>';
            var lastSec = null;
            pa[area].forEach(function (e) {
              if (e.sec !== lastSec) { lastSec = e.sec; h += '<h5 style="margin:12px 0 4px" class="dim">' + esc(e.sec) + '</h5>' }
              h += lineHtml(speakerHtml(e.speaker, e._pid), e.jp, e.i18n);
            });
          });
        }
        v.innerHTML = h;
        v.querySelectorAll('[data-sg]').forEach(function (b) { b.onclick = function () { state.sg[m] = b.dataset.sg; renderStory(m) } });
        v.querySelectorAll('[data-p]').forEach(function (b) { b.onclick = function () { var id = b.dataset.p; setMode(modeFor(id), true); go(id) } });
        window.scrollTo(0, 0);
      }
      var _renderPersonBase = renderPerson;
      renderPerson = function (p) {
        _renderPersonBase(p);
        var rows = paIndex()[p.id];
        if (!rows || !rows.length) return;
        var h = '<h3 class="sec">Parking Area lines <small>' + rows.length + '</small></h3><details><summary>Show</summary>', last = '';
        rows.forEach(function (x) {
          var k = x.g + '|' + x.area + '|' + x.e.sec;
          if (k !== last) { last = k; h += '<h5 style="margin:12px 0 4px" class="dim">' + esc((STORY_GAMES[x.g] || x.g) + ' \u00b7 ' + x.area + ' \u00b7 ' + x.e.sec) + '</h5>' }
          h += lineHtml('', x.e.jp, x.e.i18n);
        });
        document.getElementById('view').insertAdjacentHTML('beforeend', h + '</details>');
      };
      /* END_STORY_PA_UI */
"""

def inject_story_ui(html):
    boot_anchor = '/* ---------- boot ---------- */'
    if 'STORY_PA_UI' in html:
        i = html.index('/* STORY_PA_UI */')
        j = html.index(boot_anchor)
        html = html[:i].rstrip(' \t') + html[j:]
        html = html.replace(boot_anchor, STORY_UI_JS + '\n      ' + boot_anchor, 1)
        return html
    tab_anchor = '<button class="tab" role="tab" data-mode="wanderer">Wanderers</button>'
    mode_anchor = 'function setMode(m, keep) {'
    for a in (tab_anchor, boot_anchor, mode_anchor):
        if a not in html:
            return html
    html = html.replace(tab_anchor, tab_anchor + '\n        <button class="tab" role="tab" data-mode="story">Story / PA</button>\n        <button class="tab" role="tab" data-mode="poems">Poems</button>', 1)
    html = html.replace(boot_anchor, STORY_UI_JS + '\n      ' + boot_anchor, 1)
    html = html.replace(mode_anchor, mode_anchor + "\n        if (m === 'story' || m === 'poems') { return setStoryMode(m) }", 1)
    return html

TARGET_HTML = r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\zextras\Shutoko Chronicle.html'

def apply_multilingual_update():
    print(f"Reading {TARGET_HTML}...")
    with open(TARGET_HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    db = build_multilingual_database()
    db['story'] = load_story_cutscenes()
    db['pa'] = load_pa_dialogues()
    db['glossary'] = load_glossary()

    if STRICT_JP:
        strip_translations(db)
    
    db_json = json.dumps(db, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    pattern_json = r'(<script\b[^>]*\bid="?data"?[^>]*>).*?(</script>)'
    if not re.search(pattern_json, html, flags=re.S):
        raise ValueError("Could not find <script ... id=\"data\"> block!")
    html = re.sub(pattern_json, lambda m: m.group(1) + db_json + m.group(2), html, count=1, flags=re.S)
    print("Injected multilingual JSON database.")
    
    html = inject_story_ui(html)

    # 4. Remove Start Tab from navigation bar
    old_tabs_pattern = r'<button class="tab" role="tab" data-mode="home">Start</button>\s*'
    html, count = re.subn(old_tabs_pattern, '', html)

    # 4B. Add Glossary Tab
    tab_glossary = '<button class="tab" role="tab" data-mode="glossary">Glossary</button>'
    if tab_glossary not in html:
        poems_tab = '<button class="tab" role="tab" data-mode="poems">Poems</button>'
        if poems_tab in html:
            html = html.replace(poems_tab, poems_tab + '\n        ' + tab_glossary)
            print("Injected Glossary tab into navigation.")

    # 5. Multilingual JS Helpers and I18N dictionary
    js_init_marker = "var SEATKEYS = Object.keys(D.seats);"
    js_helpers = """var SEATKEYS = Object.keys(D.seats);

/* ---------- Multilingual Support ---------- */
var savedLang = 'EN';
try { savedLang = localStorage.getItem('chronicle_lang') || 'EN'; } catch(e){}
var SUPPORTED_LANGS = ['EN', 'ES', 'RU', 'CN'];
if (SUPPORTED_LANGS.indexOf(savedLang) < 0) savedLang = 'EN';

function curLang() { return state.lang || 'EN'; }
function getBio(r) { var l = curLang(); if (r.bio_i18n && r.bio_i18n[l]) return r.bio_i18n[l]; return r.text_en || ''; }
function getNick(r) { var l = curLang(); if (r.nick_i18n && r.nick_i18n[l]) return r.nick_i18n[l]; return r.nick || ''; }
function getReal(r) { var l = curLang(); if (r.real_i18n && r.real_i18n[l]) return r.real_i18n[l]; return r.real_en || r.real || ''; }
function getPersonName(p) { var l = curLang(); if (p.name_i18n && p.name_i18n[l]) return p.name_i18n[l]; return p.name_en || p.name; }
function getPersonNick(p) { var l = curLang(); if (p.nick_i18n && p.nick_i18n[l]) return p.nick_i18n[l]; return p.nick || ''; }
function getRel(r) { var l = curLang(); if (r.rel_i18n && r.rel_i18n[l]) return r.rel_i18n[l]; return r.rel || ''; }
function getTeamName(t) { var l = curLang(); if (t.name_i18n && t.name_i18n[l]) return t.name_i18n[l]; return t.name; }
function getTeamBio(t) { var l = curLang(); if (t.bio_i18n && t.bio_i18n[l]) return t.bio_i18n[l]; return t.bio25 || ''; }
function getRole(r) { var l = curLang(); if (r.role_i18n && r.role_i18n[l]) return r.role_i18n[l]; return r.role; }

var I18N_AUTO = {
  EN: { ledBy: 'Led by {leader} as {nick}', newLead: '← new leader', noLead: 'No leader marked in this game', newMembers: 'New: {members}', rec: 'rec.', secTitle: 'What the record says', secSub: 'generated from the data', whatChanged: 'What changed', chronTitle: 'Chronicle', chronSub: 'written from the records, with literal translations', teamWords: 'The team in its own words', teamWordsSub: 'original Japanese with translation, by game', recordsTitle: 'Records', recordsSub: 'original Japanese with translation, by game' },
  ES: { ledBy: 'Liderado por {leader} como {nick}', newLead: '← nuevo líder', noLead: 'Sin líder asignado en este juego', newMembers: 'Nuevos: {members}', rec: 'reg.', secTitle: 'Lo que dicen los registros', secSub: 'generado a partir de los datos', whatChanged: 'Qué cambió', chronTitle: 'Crónica', chronSub: 'escrito a partir de los registros, con traducciones literales', teamWords: 'El equipo en sus propias palabras', teamWordsSub: 'japonés original con traducción, por juego', recordsTitle: 'Registros', recordsSub: 'japonés original con traducción, por juego' },
  RU: { ledBy: 'Во главе с {leader} под именем {nick}', newLead: '← новый лидер', noLead: 'В этой игре лидер не указан', newMembers: 'Новые: {members}', rec: 'зап.', secTitle: 'Что говорят записи', secSub: 'сгенерировано на основе данных', whatChanged: 'Что изменилось', chronTitle: 'Хроника', chronSub: 'составлено по записям, с буквальным переводом', teamWords: 'Команда о себе', teamWordsSub: 'оригинальный японский с переводом, по играм', recordsTitle: 'Записи', recordsSub: 'оригинальный японский с переводом, по играм' },
  CN: { ledBy: '由 {leader} 领衔（称号：{nick}）', newLead: '← 新队长', noLead: '本代无明确队长', newMembers: '新加入：{members}', rec: '条记录', secTitle: '档案记载', secSub: '由数据自动生成', whatChanged: '历史变迁', chronTitle: '编年史', chronSub: '根据记录整理，附直译', teamWords: '车队自述', teamWordsSub: '日文原版与译文对照（按各代）', recordsTitle: '历史记录', recordsSub: '日文原版与译文对照（按各代）' }
};
"""
    if "/* ---------- Multilingual Support ---------- */" not in html:
        html = html.replace(js_init_marker, js_helpers)
    else:
        pattern_helpers = r'var SEATKEYS = Object\.keys\(D\.seats\);.*?/\* ==============================================================================\s+STAGE 3 & 4.*?\*/'
        html = re.sub(pattern_helpers, js_helpers.strip(), html, count=1, flags=re.DOTALL)

    # 5B. Taxonomy THEMES and THEME_NOTE
    tax_title_and_themes = """var TAX_TITLE = {
  pillar: { 'MARTIAL': 'Martial Philosophy', 'FEUDAL': 'Feudal Allegories', 'SUPERNATURAL': 'Supernatural & Folklore', 'INDUSTRY': 'Industry & Real-World' },
  motivator: { 'GRIEF': 'Grief & Loss', 'VENDETTA': 'Vendetta & Obsession', 'ESCAPE': 'The Escape & The Void', 'BOND': 'Devotion & Pure Craft' }
};

var THEMES={
  person:[
    ['p:MARTIAL','Martial'],['p:FEUDAL','Feudal'],['p:SUPERNATURAL','Supernatural'],['p:INDUSTRY','Industry'],
    ['m:GRIEF','Grief'],['m:VENDETTA','Vendetta'],['m:ESCAPE','Escape'],['m:BOND','Bond'],
    ['renamed','Changed byname'],['moved','Changed team'],['rose','Rose in rank'],['fell','Fell in rank'],['drifted','Wanderer ↔ team'],['returned','Gap years'],['sharedname','Byname worn by others'],['respelled','Name respelled'],['long','4+ games'],['once','One game']
  ],
  team:[
    ['p:MARTIAL','Martial'],['p:FEUDAL','Feudal'],['p:SUPERNATURAL','Supernatural'],['p:INDUSTRY','Industry'],
    ['m:GRIEF','Grief'],['m:VENDETTA','Vendetta'],['m:ESCAPE','Escape'],['m:BOND','Bond'],
    ['succession','Leader changed hands'],['numbered','Numbered titles'],['returned','Gap years'],['long','5+ games'],['once','One game']
  ]
};

var THEME_NOTE={
  'p:MARTIAL': 'Pillar: Martial Philosophy (Bushido, composure, sovereign lineages).',
  'p:FEUDAL': 'Pillar: Feudal Allegories (Clan retainers, warlords, Shinsengumi).',
  'p:SUPERNATURAL': 'Pillar: Supernatural & Folklore (Tsukumogami, Ikiryō, ghosts, demonology).',
  'p:INDUSTRY': 'Pillar: Industry & Real-World (Tuning shops, mechanics, real racers).',
  'm:GRIEF': 'Motivator: Grief & Loss (Memorial rituals, departed friends, shattered eras).',
  'm:VENDETTA': 'Motivator: Vendetta & Obsession (Unavenged defeats, grudges, score-settling).',
  'm:ESCAPE': 'Motivator: The Escape & The Void (Fleeing mundane life, isolation, fading youth).',
  'm:BOND': 'Motivator: Devotion & Pure Craft (Brotherhood, mentorship, pure driving dialogue).',
  renamed:'Same person, different byname (numbered titles ignored).',
  moved:'Seen under more than one team.',
  rose:'Role went up between games.',
  fell:'Role went down between games.',
  drifted:'Moved between a team and wandering.',
  returned:'Missing for at least one game in between.',
  sharedname:'Someone else also carried this byname.',
  respelled:'The real name is spelled differently between games; treated as the same person.',
  long:'Appears in 4 or more games.',
  once:'Appears in one game only.',
  succession:'More than one person led this team over the series.',
  numbered:'Members hold numbered titles.'
};"""
    pat_themes = r'(?:var TAX_TITLE\s*=\s*\{.*?\};\s*)?var THEMES=\{.*?\};\s*var THEME_NOTE=\{.*?\};'
    html, count = re.subn(pat_themes, tax_title_and_themes, html, count=1, flags=re.DOTALL)

    # 6. Update state initialization
    state_pattern = r"var state=\{mode:'(?:home|team)',sel:null,q:'',themes:\{\}(?:,lang:savedLang)?\};"
    html = re.sub(state_pattern, "var state={mode:'team',sel:null,q:'',themes:{},lang:savedLang};", html)

    # 7. Update haystack search logic
    new_haystack = """function haystack(e){
  if(e.kind==='team') {
    var str = tk(e.name)+' '+e.alt.map(tk).join(' ');
    if (e.name_i18n) Object.keys(e.name_i18n).forEach(function(l){ str += ' ' + tk(e.name_i18n[l]); });
    return str.toUpperCase();
  }
  var s=nk(e.name)+' '+tk(e.name_en||'')+' '+nk(e.disp)+' '+tk(e.nick||'')+' ';
  if (e.name_i18n) Object.keys(e.name_i18n).forEach(function(l){ s += tk(e.name_i18n[l]) + ' '; });
  if (e.nick_i18n) Object.keys(e.nick_i18n).forEach(function(l){ s += tk(e.nick_i18n[l]) + ' '; });
  e.recs.forEach(function(i){
    var r=R[i];
    s+=nk(r.disp)+' '+tk(r.nick||'')+' '+tk(r.team)+' '+nk(r.real)+' '+tk(r.real_en||'')+' ';
    if (r.nick_i18n) Object.keys(r.nick_i18n).forEach(function(l){ s += tk(r.nick_i18n[l]) + ' '; });
    if (r.real_i18n) Object.keys(r.real_i18n).forEach(function(l){ s += tk(r.real_i18n[l]) + ' '; });
  });
  return s.toUpperCase();
}"""
    pattern_haystack = r'function haystack\(e\)\{.*?return s\.toUpperCase\(\);\s*\}'
    html = re.sub(pattern_haystack, new_haystack, html, count=1, flags=re.DOTALL)

    # 8. Update renderRail (always show rail, no home mode)
    old_rail_home = """  rail.hidden = mode==='home';
  document.querySelector('.layout').style.gridTemplateColumns = mode==='home' ? 'minmax(0,1fr)' : '';
  if(mode==='home') return;"""
    new_rail_home = """  rail.hidden = false;
  document.querySelector('.layout').style.gridTemplateColumns = '';"""
    if old_rail_home in html:
        html = html.replace(old_rail_home, new_rail_home)

    # 9. Update renderRail item titles
    new_rail_titles = """    var mainTitle = e.kind==='team' ? getTeamName(e) : getPersonName(e);
    var subJp = (e.kind==='person' && mainTitle && mainTitle !== e.name) ? e.name : '';"""
    old_rail_titles_pat = r'var mainTitle\s*=\s*e\.kind===\'team\'\s*\?\s*e\.name\s*:\s*\(e\.name_en\s*\|\|\s*e\.name\);\s*var subJp\s*=\s*\(e\.kind===\'person\'\s*&&\s*e\.name_en\s*&&\s*e\.name_en\s*!==\s*e\.name\)\s*\?\s*e\.name\s*:\s*\'\';'
    html = re.sub(old_rail_titles_pat, new_rail_titles, html, count=1)

    # 9B. Update renderRail chips loop with taxonomy styling
    new_chips_loop = """  THEMES[kind].forEach(function(t){
    var n=base.filter(function(e){return e.themes.indexOf(t[0])>=0}).length;
    if(!n) return;
    var b=document.createElement('button'); b.type='button'; b.className='chip';
    if(t[0].indexOf('p:') === 0) b.classList.add('chip-pillar');
    else if(t[0].indexOf('m:') === 0) b.classList.add('chip-motivator');
    b.setAttribute('aria-pressed', state.themes[t[0]]?'true':'false'); b.title=THEME_NOTE[t[0]]||'';
    b.innerHTML=esc(t[1])+' <b>'+n+'</b>';
    b.onclick=function(){state.themes[t[0]]=!state.themes[t[0]];renderRail()};
    chips.appendChild(b);
  });"""
    pat_chips_loop = r'THEMES\[kind\]\.forEach\(function\(t\)\{.*?chips\.appendChild\(b\);\s*\}\);'
    html, count = re.subn(pat_chips_loop, new_chips_loop, html, count=1, flags=re.DOTALL)

    # 10. Update go(id, noScroll)
    old_go_home = "if(!id){renderHome();return}"
    new_go_home = "if(!id){renderPrompt();return}"
    if old_go_home in html:
        html = html.replace(old_go_home, new_go_home)

    # 11. Update renderRailSelectionOnly
    old_sel_only = "if(state.mode!=='home') renderRail();"
    new_sel_only = "renderRail();"
    if old_sel_only in html:
        html = html.replace(old_sel_only, new_sel_only)

    # 12. Update setMode
    old_set_mode = "if(m==='home') renderHome(); else if(!state.sel) renderPrompt();"
    new_set_mode = "if(!state.sel) renderPrompt();"
    if old_set_mode in html:
        html = html.replace(old_set_mode, new_set_mode)

    # 13. Update modeFor
    old_mode_for = "function modeFor(id){\n  if(id.charAt(0)==='t') return 'team';\n  if(id.charAt(0)==='p'){var p=P[id]; return p.roles.indexOf('Boss')>=0?'boss':'wanderer'}\n  return 'home';\n}"
    new_mode_for = "function modeFor(id){\n  if(id.charAt(0)==='t') return 'team';\n  if(id.charAt(0)==='p'){var p=P[id]; return p.roles.indexOf('Boss')>=0?'boss':'wanderer'}\n  return 'team';\n}"
    if old_mode_for in html:
        html = html.replace(old_mode_for, new_mode_for)

    # 14. Delete renderHome and card function block
    pattern_home_func = r'/\* ---------- home ---------- \*/\s*function renderHome\(\)\{.*?function card\(kind,k,h,d,id\)\{.*?\}\s*'
    html, count = re.subn(pattern_home_func, '', html, count=1, flags=re.DOTALL)

    # 14B. Update head function to render taxonomy badges
    new_head_func = """function head(eyebrow,title,aka,meta,titleJp,entity){
  var taxBadge = '';
  if (entity && (entity.pillar || entity.motivator)) {
    var pTitle = (TAX_TITLE.pillar && TAX_TITLE.pillar[entity.pillar]) || entity.pillar;
    var mTitle = (TAX_TITLE.motivator && TAX_TITLE.motivator[entity.motivator]) || entity.motivator;
    taxBadge = '<div class="tax-badge">'
      + (entity.pillar ? '<span class="tax-tag pillar-tag" title="' + esc(THEME_NOTE['p:' + entity.pillar] || '') + '">🏛 ' + esc(pTitle) + '</span>' : '')
      + (entity.motivator ? '<span class="tax-tag motivator-tag" title="' + esc(THEME_NOTE['m:' + entity.motivator] || '') + '">⚡ ' + esc(mTitle) + '</span>' : '')
      + '</div>';
  }
  return '<button type="button" class="chip back">← Back to list</button><p class="eyebrow" style="margin-top:10px">'+esc(eyebrow)+'</p><h2 class="title">'+esc(title)+(titleJp?' <span class="jp-sub">&middot; '+esc(titleJp)+'</span>':'')+'</h2>'+taxBadge+(aka?'<p class="aka">'+esc(aka)+'</p>':'')+'<div class="metaline">'+meta.map(function(m){return '<span>'+esc(m)+'</span>'}).join('')+'</div>';
}"""
    pat_head_func = r'function head\(eyebrow,title,aka,meta,titleJp(?:,entity)?\)\{.*?return \'<button type="button" class="chip back">.*?\</div>\';\s*\}'
    html, count = re.subn(pat_head_func, new_head_func, html, count=1, flags=re.DOTALL)

    # 14C. Update renderTeam and renderPerson head calls
    new_team_head = """  var activeTeamName = getTeamName(t);
  var teamSubJp = (t.name && activeTeamName !== t.name) ? t.name : '';
  var h = head('Team', activeTeamName, t.alt.length ? 'Also spelled: ' + t.alt.join(', ') : '', [
    span(t.games),
    t.games.length + ' of ' + G.length + ' games',
    t.recs.length + ' records',
    order.length + ' people'
  ], teamSubJp, t);"""
    pat_team_head = r'(?:var activeTeamName = getTeamName\(t\);\s*var teamSubJp = \(t\.name && activeTeamName !== t\.name\) \? t\.name : \'\';\s*)?var h = head\(\'Team\', (?:activeTeamName|t\.name), t\.alt\.length \? \'Also spelled: \' \+ t\.alt\.join\(\', \'\) : \'\', \[\s*span\(t\.games\),\s*t\.games\.length \+ \' of \' \+ G\.length \+ \' games\',\s*t\.recs\.length \+ \' records\',\s*order\.length \+ \' people\'\s*\](?:,\s*teamSubJp,\s*t)?\);'
    html, count = re.subn(pat_team_head, new_team_head, html, count=1, flags=re.DOTALL)

    new_person_head = "var h = head(eyebrow, titleEn, akaPairs.join(' · '), meta, titleJp, p);"
    pat_person_head = r'var h = head\(eyebrow, titleEn, akaPairs\.join\(\' · \'\), meta, titleJp(?:, p)?\);'
    html, count = re.subn(pat_person_head, new_person_head, html, count=1)

    # 15. Update recDetails with multilingual getters
    new_rec_details = """function recDetails(r,open){
  var activeNick = getNick(r);
  var monikerJp = clean(r.disp);
  var isDiff = activeNick && nk(activeNick).toUpperCase() !== nk(monikerJp).toUpperCase();
  var summaryTitle = activeNick || monikerJp;
  var summarySub = isDiff ? ' <span class="jp-sub">&middot; ' + esc(monikerJp) + '</span>' : '';
  var s='<details class="rec"'+(open?' open':'')+'><summary><span class="mono">'+esc(glf(r.g))+'</span><b class="rec-title">'+esc(summaryTitle)+'</b>'+summarySub+'<span class="dim">'+esc(r.team)+' · '+esc(getRole(r))+'</span></summary><div class="rec-body">';
  var activeReal = getReal(r);
  var realLockup = activeReal ? esc(activeReal) + (r.real && r.real !== activeReal && curLang() !== 'CN' ? ' <span class="jp-sub">(' + esc(r.real) + ')</span>' : '') : esc(r.real || '');
  s+='<div class="rec-head">'+esc(r.id)+(r.car?' · '+esc(r.car):'')+(r.plate?' · '+esc(r.plate):'')+(realLockup?' · '+realLockup:'')+'</div>';
  if(r.notes) s+='<p class="dim" style="font-size:12px;margin:2px 0 4px">'+esc(r.notes)+'</p>';
  if(r.text) s+='<p class="jp">'+esc(r.text)+'</p>';
  var activeBio = getBio(r);
  if(activeBio && nk(activeBio).toUpperCase() !== nk(r.text||'').toUpperCase()) s+='<p class="en-bio">'+esc(activeBio)+'</p>';
  if(!r.text && !activeBio) s+='<p class="dim">No text in the data for this record.</p>';
  var activeRel = getRel(r);
  if(activeRel) s+='<p class="en">Relationship note: '+esc(activeRel)+'</p>';
  if(r.rumor) s+='<p class="en jp">Rumor: '+esc(r.rumor)+'</p>';
  return s+'</div></details>';
}"""
    pattern_rec_details = r'function recDetails\(r,open\)\{.*?return s\+\'</div></details>\';\s*\}'
    html = re.sub(pattern_rec_details, new_rec_details, html, count=1, flags=re.DOTALL)

    # 16. Universal getTeamSeats
    new_get_team_seats = """function getTeamSeats(t, mem, maxn) {
  var isRG = (t.name === 'ROLLING GUY');
  var isNumbered = (t.themes && t.themes.indexOf('numbered') >= 0);

  if (isRG || isNumbered) {
    var pids = Object.keys(mem);
    var numSet = {};
    var hasMaster = false;

    function inspectDisp(disp) {
      if (!disp) return;
      var m = disp.match(/([0-9０-９]+)号/);
      if (m) numSet[parseInt(m[1].normalize('NFKC'), 10)] = true;
      if (disp.indexOf('マスター') >= 0) hasMaster = true;
    }

    t.recs.forEach(function(i){ inspectDisp(R[i].disp); });
    pids.forEach(function(pid){
      P[pid].recs.forEach(function(rid){ inspectDisp(R[rid].disp); });
    });

    var nums = Object.keys(numSet).map(Number).sort(function(a,b){return a-b});
    if (nums.length || hasMaster) {
      var seats = nums.map(function(n){
        var isLeader = (n === 1);
        var en = 'Seat #' + n + (isLeader ? ' (Leader)' : '');
        var jp = isRG ? (isLeader ? '☆ローリング野郎1号' : 'ローリング野郎' + n + '号') : (n + '号');
        return {
          key: String(n),
          en: en,
          jp: jp,
          matches: function(disp) {
            if (!disp) return false;
            var m = disp.match(/([0-9０-９]+)号/);
            return m && parseInt(m[1].normalize('NFKC'), 10) === n;
          }
        };
      });

      if (hasMaster || isRG) {
        seats.push({
          key: 'master',
          en: 'Founder / Master',
          jp: isRG ? 'ローリングマスター' : 'マスター',
          matches: function(disp) {
            return disp && disp.indexOf('マスター') >= 0;
          }
        });
      }

      return seats;
    }
  }

  // Universal seats for all teams
  var seats = [];
  var limit = (maxn && maxn > 0) ? maxn : 1;
  for (var n = 1; n <= limit; n++) {
    var isLeader = (n === 1);
    var en = 'Seat #' + n + (isLeader ? ' (Leader)' : '');
    var jp = isLeader ? '☆第1席 (リーダー)' : ('第' + n + '席');
    seats.push({
      key: String(n),
      slotIndex: n - 1,
      en: en,
      jp: jp
    });
  }
  return seats;
}"""
    pattern_get_team_seats = r'function getTeamSeats\(t,\s*mem.*?\)\s*\{.*?(?=\nfunction renderTeam\()'
    html, count = re.subn(pattern_get_team_seats, new_get_team_seats, html, count=1, flags=re.DOTALL)

    # 17. Universal seat matrix & toggle buttons in renderTeam
    pattern_render_team_seats = r'var seats\s*=\s*getTeamSeats\(t,\s*mem.*?\);.*?(?=\s+// --- BY DRIVER MATRIX ---)'
    new_render_team_seats = """var isRG = (t.name === 'ROLLING GUY');
  var seats = getTeamSeats(t, mem, maxn);
  var activeView = teamViewPref[t.name] || (isRG ? 'seat' : 'driver');

  // Header & View Toggle
  h += '<h3 class="sec">Who held which seat <small>read left to right; titles are shown as written</small></h3>';
  h += '<div class="chips" style="margin-bottom:12px">'
    + '<button type="button" class="chip" data-tv="seat" aria-pressed="' + (activeView === 'seat') + '">💺 By Seat (Succession)</button>'
    + '<button type="button" class="chip" data-tv="driver" aria-pressed="' + (activeView === 'driver') + '">👤 By Driver (Careers)</button>'
    + '</div>';

  h += '<div class="scroll"><table class="tg">' + gridHead() + '<tbody>';

  if (seats && activeView === 'seat') {
    // --- BY SEAT SUCCESSION MATRIX ---
    var pids = Object.keys(mem);
    seats.forEach(function(s){
      h += '<tr><th class="rowh" scope="row"><span class="n">' + esc(s.en) + '</span><span class="e jp">' + esc(s.jp) + '</span></th>';
      var lastTeamPid = null;
      G.forEach(function(g, gi){
        var foundR = null;
        if (s.slotIndex !== undefined) {
          var gameRecs = t.recs.map(function(i){ return R[i]; }).filter(function(r){ return r.g === gi; });
          gameRecs.sort(function(a, b){
            return (roleOrder(a.role) - roleOrder(b.role)) || (a.id < b.id ? -1 : 1);
          });
          if (s.slotIndex < gameRecs.length) {
            foundR = gameRecs[s.slotIndex];
          }
        } else {
          for (var i = 0; i < t.recs.length; i++) {
            var r = R[t.recs[i]];
            if (r.g === gi && s.matches(r.disp)) { foundR = r; break; }
          }
          if (!foundR) {
            for (var pi = 0; pi < pids.length; pi++) {
              var pid = pids[pi];
              var precs = P[pid].recs;
              for (var ri = 0; ri < precs.length; ri++) {
                var pr = R[precs[ri]];
                if (pr.g === gi && s.matches(pr.disp)) { foundR = pr; break; }
              }
              if (foundR) break;
            }
          }
        }

        if (foundR) {
          var p = P[foundR.pid];
          var cellClass = '';
          if (foundR.team !== t.name) {
            cellClass = 'k-else';
          } else if (lastTeamPid && lastTeamPid !== foundR.pid) {
            cellClass = 'k-role';
            lastTeamPid = foundR.pid;
          } else if (!lastTeamPid) {
            cellClass = 'k-enter';
            lastTeamPid = foundR.pid;
          }

          var meta = [];
          if (foundR.team !== t.name) meta.push(foundR.team);
          if (foundR.car) meta.push(foundR.car);

          var activeNick = getNick(foundR);
          var monikerLockup = (activeNick && nk(activeNick).toUpperCase() !== nk(foundR.disp).toUpperCase())
            ? esc(activeNick) + ' <span class="jp-sub">&middot; ' + esc(clean(foundR.disp)) + '</span>'
            : esc(clean(foundR.disp));

          h += '<td class="' + cellClass + '"><span class="cell">'
            + '<button type="button" class="linkbtn t" data-p="' + p.id + '">' + esc(getPersonName(p)) + '</button>'
            + (getPersonName(p) && getPersonName(p) !== p.name && curLang() !== 'CN' ? '<span class="dim" style="display:block;font-size:10px;">' + esc(p.name) + '</span>' : '')
            + '<span class="m">' + monikerLockup + (meta.length ? ' · ' + esc(meta.join(' · ')) : '') + '</span>'
            + '</span></td>';
        } else {
          h += '<td><span class="dim">—</span></td>';
        }
      });
      h += '</tr>';
    });
  } else {"""
    html, count = re.subn(pattern_render_team_seats, new_render_team_seats, html, count=1, flags=re.DOTALL)

    # 18. Localized teamAuto
    new_team_auto = """function teamAuto(t,mem,order){
  var lang = curLang();
  var dict = I18N_AUTO[lang] || I18N_AUTO['EN'];
  var out = '<ul class="log">';
  var lastLead = null;
  t.games.forEach(function(g){
    var rs = t.recs.map(function(i){ return R[i]; }).filter(function(r){ return r.g === g; });
    var lead = rs.filter(function(r){ return r.role === 'Leader'; })[0];
    var line = [];
    if (lead) {
      var lp = P[lead.pid];
      var lpName = getPersonName(lp);
      var leaderLockup = '<b class="jp">' + esc(lpName) + '</b>' + (lp.name && lp.name !== lpName && lang !== 'CN' ? ' <span class="jp-sub">(' + esc(lp.name) + ')</span>' : '');
      
      var moniker = getNick(lead);
      var dispClean = clean(lead.disp);
      var monikerLockup = '<span class="jp">' + esc(moniker || dispClean) + '</span>' + (moniker && nk(moniker).toUpperCase() !== nk(dispClean).toUpperCase() && lang !== 'CN' ? ' <span class="jp-sub">(' + esc(dispClean) + ')</span>' : '');
      
      var leadStr = dict.ledBy.replace('{leader}', leaderLockup).replace('{nick}', monikerLockup);
      if (lastLead && lastLead !== lead.pid) {
        leadStr += ' <span class="arrow">' + esc(dict.newLead) + '</span>';
      }
      line.push(leadStr);
      lastLead = lead.pid;
    } else {
      line.push(dict.noLead);
    }
    
    var ids = rs.map(function(r){ return r.pid; });
    var prevIds = t.recs.map(function(i){ return R[i]; }).filter(function(r){ return r.g < g; }).map(function(r){ return r.pid; });
    var seenBefore = {}; prevIds.forEach(function(p){ seenBefore[p] = 1; });
    var joined = ids.filter(function(p, i){ return !seenBefore[p] && ids.indexOf(p) === i; });
    if (prevIds.length && joined.length) {
      var joinSep = (lang === 'CN' ? '、' : ', ');
      var joinedStr = joined.map(function(pid){
        var q = P[pid];
        var qName = getPersonName(q);
        return '<span class="jp">' + esc(qName) + '</span>' + (q.name && q.name !== qName && lang !== 'CN' ? ' <span class="jp-sub">(' + esc(q.name) + ')</span>' : '');
      }).join(joinSep);
      line.push(dict.newMembers.replace('{members}', joinedStr));
    }
    
    var sep = (lang === 'CN' ? '。' : '. ');
    out += '<li><span class="w">' + esc(glf(g)) + ' · ' + rs.length + ' ' + esc(dict.rec) + '</span><span>' + line.join(sep) + '</span></li>';
  });
  return out + '</ul>';
}"""
    pattern_team_auto = r'function teamAuto\(t,\s*mem,\s*order\)\{.*?return out\s*\+\s*\'</ul>\';\s*\}'
    html = re.sub(pattern_team_auto, new_team_auto, html, count=1, flags=re.DOTALL)

    # 19. Update renderTeam bottom (standard "What the record says", "In their own words", "Records")
    new_render_team_bottom = """  // story
  var dict = I18N_AUTO[curLang()] || I18N_AUTO['EN'];
  h += '<h3 class="sec">' + esc(dict.secTitle) + '<small>' + esc(dict.secSub) + '</small></h3>';
  h += '<div class="auto">' + teamAuto(t, mem, order) + '</div>';

  // in their own words
  if (t.bios && t.bios.length) {
    h += '<h3 class="sec">' + esc(dict.teamWords) + '<small>' + esc(dict.teamWordsSub) + '</small></h3>';
    t.bios.forEach(function(tb){
      var activeBio = (tb.i18n && tb.i18n[curLang()]) || (tb.i18n && tb.i18n['EN']) || '';
      var out = '<details class="rec" open><summary><b>' + esc(glf(tb.g)) + '</b></summary><div class="rec-body">';
      if (tb.jp) out += '<p class="jp">' + esc(tb.jp) + '</p>';
      if (activeBio && nk(activeBio).toUpperCase() !== nk(tb.jp || '').toUpperCase()) {
        out += '<p class="en-bio">' + esc(activeBio) + '</p>';
      }
      out += '</div></details>';
      h += out;
    });
  } else if (t.bio25) {
    h += '<h3 class="sec">' + esc(dict.teamWords) + '<small>' + esc(dict.teamWordsSub) + '</small></h3><div class="auto"><p class="jp" style="max-width:70ch">' + esc(t.bio25) + '</p></div>';
  }

  // records
  h += '<h3 class="sec">' + esc(dict.recordsTitle) + '<small>' + esc(dict.recordsSub) + '</small></h3>';
  G.forEach(function(g, gi){
    var rs = t.recs.filter(function(i){ return R[i].g === gi; }).map(function(i){ return R[i]; });
    if (!rs.length) return;
    h += '<details class="rec"><summary><b>' + esc(glf(gi)) + '</b><span class="dim">' + rs.length + ' records</span></summary><div class="rec-body">' + rs.map(function(r){
      var activeReal = getReal(r); var realLockup = activeReal ? esc(activeReal) + (r.real && r.real !== activeReal && curLang() !== 'CN' ? ' (' + esc(r.real) + ')' : '') : esc(r.real || '');
      var activeNick = getNick(r);
      var monikerLockup = (activeNick && nk(activeNick).toUpperCase() !== nk(r.disp).toUpperCase()) ? esc(activeNick) + ' <span class="jp-sub">&middot; ' + esc(clean(r.disp)) + '</span>' : esc(clean(r.disp));
      var out = '<div class="rr"><div class="rec-head">' + esc(r.id) + ' · ' + esc(getRole(r)) + (r.car ? ' · ' + esc(r.car) : '') + (r.plate ? ' · ' + esc(r.plate) : '') + (realLockup ? ' · ' + realLockup : '') + '</div>';
      if (r.notes) out += '<p class="dim" style="font-size:12px;margin:2px 0 4px">' + esc(r.notes) + '</p>';
      out += '<p class="jp"><b>' + monikerLockup + '</b>' + (r.text ? ' ' + esc(r.text) : '') + '</p>';
      var activeBio = getBio(r); if (activeBio && nk(activeBio).toUpperCase() !== nk(r.text||'').toUpperCase()) out += '<p class="en-bio">' + esc(activeBio) + '</p>';
      var activeRel = getRel(r); if (activeRel) out += '<p class="en">Relationship note: ' + esc(activeRel) + '</p>';
      return out + '</div>';
    }).join('') + '</div></details>';
  });"""
    pattern_render_team_bottom = r'// story\s+var (?:dict = I18N_AUTO|S = STORIES).*?\}\)\.join\(\'\'\)\s*\+\s*\'</div></details>\';\s*\}\);'
    html, count = re.subn(pattern_render_team_bottom, new_render_team_bottom, html, count=1, flags=re.DOTALL)

    # 20. Update renderPerson story with standard "What changed"
    old_person_story = """  // story
  var key='person:'+p.name, S=STORIES[key], SS=null;
  if(!S){p.seats.forEach(function(d){if(STORIES['seat:'+seatName(d)]) SS=seatName(d)})}
  h+='<h3 class="sec">'+((S||SS)?'Chronicle':'What changed')+'<small>'+((S||SS)?'written from the records, with literal translations':'generated from the data')+'</small></h3>';
  if(S) h+='<div class="story">'+S()+'</div>';
  else if(SS) h+='<div class="story">'+STORIES['seat:'+SS]()+'</div>';
  else h+='<div class="auto">'+personAuto(p,bg)+'</div>';
  if(S&&!p.seats.length) {}"""
    new_person_story = """  // story
  var dict = I18N_AUTO[curLang()] || I18N_AUTO['EN'];
  h += '<h3 class="sec">' + esc(dict.whatChanged || 'What changed') + '<small>' + esc(dict.secSub) + '</small></h3>';
  h += '<div class="auto">' + personAuto(p, bg) + '</div>';"""
    if old_person_story in html:
        html = html.replace(old_person_story, new_person_story)
    else:
        pattern_person_story = r'// story\s+var key=\'person:\'\+p\.name, S=STORIES\[key\], SS=null;.*?else h\+=\'<div class="auto">\'+personAuto\(p,bg\)+\'</div>\';(?:\s*if\(S&&!p\.seats\.length\)\s*\{\})?'
        html, count = re.subn(pattern_person_story, new_person_story.strip(), html, count=1, flags=re.DOTALL)

    # 21. Update personAuto with multilingual getters
    new_person_auto = """function personAuto(p,bg){
  var out='<ul class="log">', prev=null;
  p.games.forEach(function(g){
    var r=bg[g][0];
    var msgs=[];
    var activeNick = getNick(r);
    var mLockup = activeNick && nk(activeNick).toUpperCase() !== nk(r.disp).toUpperCase() ? esc(activeNick) + ' <span class="jp-sub">(' + esc(clean(r.disp)) + ')</span>' : esc(clean(r.disp));
    if(!prev){msgs.push('First seen as <b>'+mLockup+'</b>, '+esc(getRole(r))+(PSEUDO[r.tk]?'':' of '+esc(r.team))+(r.car?', '+esc(r.car):''))}
    else{
      if(g-prev.g>1) msgs.push('Not in '+(g-prev.g-1)+' game'+(g-prev.g>2?'s':'')+' in between');
      if(!isNum(prev.disp)&&!isNum(r.disp)&&nk(prev.disp)!==nk(r.disp)){
        var prevNick = getNick(prev);
        var prevLockup = prevNick && nk(prevNick).toUpperCase() !== nk(prev.disp).toUpperCase() ? esc(prevNick) + ' (' + esc(clean(prev.disp)) + ')' : esc(clean(prev.disp));
        var curLockup = activeNick && nk(activeNick).toUpperCase() !== nk(r.disp).toUpperCase() ? esc(activeNick) + ' (' + esc(clean(r.disp)) + ')' : esc(clean(r.disp));
        msgs.push('byname <span>'+prevLockup+'</span> <span class="arrow">→</span> <span>'+curLockup+'</span>');
      }
      if(prev.tk!==r.tk) msgs.push('team '+esc(prev.team)+' <span class="arrow">→</span> '+esc(r.team));
      if(prev.role!==r.role) msgs.push('role '+esc(getRole(prev))+' <span class="arrow">→</span> '+esc(getRole(r)));
      var sb01=(prev.g===4||r.g===4);
      if(!sb01&&r.car&&prev.car&&r.car!==prev.car) msgs.push('car '+esc(prev.car)+' <span class="arrow">→</span> '+esc(r.car));
      if(!sb01&&prev.plate&&r.plate){var a=prev.plate.split(' ')[0],b=r.plate.split(' ')[0]; if(a!==b) msgs.push('plate region '+esc(a)+' <span class="arrow">→</span> '+esc(b))}
      if(!msgs.length) msgs.push('<span class="dim">no change in byname, team, role or car</span>');
    }
    if(bg[g].length>1) msgs.push(bg[g].length+' records in this game');
    out+='<li><span class="w">'+esc(prev?gl(prev.g)+' → '+gl(g):glf(g))+'</span><span>'+msgs.join('; ')+'</span></li>';
    prev=r;
  });
  return out+'</ul>';
}"""
    pattern_person_auto = r'function personAuto\(p,bg\)\{.*?return out\+\'</ul>\';\s*\}'
    html = re.sub(pattern_person_auto, new_person_auto, html, count=1, flags=re.DOTALL)

    # 22. Remove renderSeat story
    old_seat_story = "  var S=STORIES['seat:'+name];\n  if(S) h+='<h3 class=\"sec\">Chronicle<small>written from the records, with literal translations</small></h3><div class=\"story\">'+S()+'</div>';"
    if old_seat_story in html:
        html = html.replace(old_seat_story, '')

    # 23. Remove STORIES block
    pattern_stories = r'/\* ---------- written chronicles ---------- \*/\s*function jq\(ja,en,ref\)\{.*?var STORIES=\{\};.*?(?=/\* ---------- boot ---------- \*/)'
    html, count = re.subn(pattern_stories, '', html, count=1, flags=re.DOTALL)

    # 24. Update boot IIFE to default to 'team'
    old_boot = "else setMode('home');"
    new_boot = "else setMode('team');"
    if old_boot in html:
        html = html.replace(old_boot, new_boot)

    # 25. Update renderCurrent callback
    old_render_cur = """  function renderCurrent(){
    renderRail();
    if(state.sel) go(state.sel, true);
    else if(state.mode==='home') renderHome();
    else renderPrompt();
  }"""
    new_render_cur = """  function renderCurrent(){
    renderRail();
    if(state.sel) go(state.sel, true);
    else renderPrompt();
  }"""
    if old_render_cur in html:
        html = html.replace(old_render_cur, new_render_cur)

    # 26. Remove 'English' in 'original Japanese with English translation, by game' everywhere
    old_en_trans = '<small>original Japanese with English translation, by game</small>'
    new_trans = '<small>original Japanese with translation, by game</small>'
    if old_en_trans in html:
        html = html.replace(old_en_trans, new_trans)

    # 27. Inject Glossary JS into the frontend
    if 'function setGlossaryMode()' not in html:
        boot_marker = '/* ---------- boot ---------- */'
        if boot_marker in html:
            html = html.replace(boot_marker, GLOSSARY_JS + '\n      ' + boot_marker)
            print("Injected Glossary UI JavaScript.")

    with open(TARGET_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"\nSuccessfully updated {TARGET_HTML}!")
    print(f"File size: {os.path.getsize(TARGET_HTML):,} bytes.")

if __name__ == '__main__':
    apply_multilingual_update()