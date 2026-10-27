# -*- coding: utf-8 -*-
"""
Multilingual Chronicle Database Builder & HTML Updater
Plugs in multilingual capabilities (CN, EN, ES, RU) mirroring English display.
Includes commented-out hooks for PA dialogues and story cutscenes.
"""

import os, sys, csv, json, re, unicodedata
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\scratch')

from en_layer_data import build_master_name_dict, extract_all_en_bios
from build_chronicle import (
    GAMES, REAL_NAME_ALIASES, SPECIAL_ENTITIES, MONIKER_SYNONYMS, KB_NICKS,
    clean_real, clean_handle, clean_nick, clean_team
)

BASE_TR = r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\zextras\chronicle_stuff\TR'
TARGET_HTML = r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\zextras\Shutoko Chronicle.html'

GAMES_META = [
    ("SB1", "00_SB1", "Shutoko Battle Rival Manifest Master - SB1.csv", "Shutoko Battle Rival Manifest Master - Team Manifest SB(1999).csv"),
    ("SB2", "01_SB2", "Shutoko Battle Rival Manifest Master - SB2.csv", "Shutoko Battle Rival Manifest Master - Team Manifest SB2.csv"),
    ("SB0", "02_SB0", "Shutoko Battle Rival Manifest Master - SB0.csv", "Shutoko Battle Rival Manifest Master - Team Manifest SB0.csv"),
    ("KB1", "04_KB1", "Kaido Battle Rival Manifest.csv", None),
    ("SB01", "03_SB01", "Shutoko Battle Rival Manifest Master - SB01.csv", "Shutoko Battle Rival Manifest Master - Team Manifest SB01.csv"),
    ("KB2", "05_KB2", "Kaido Battle 2 Rival Manifest.csv", None),
    ("KB3", "06_KB3", "Kaido Battle 3 Rival Manifest.csv", None),
    ("PSP", "09_SB-PSP", "Shutoko Battle Rival Manifest Master - SB(PSP).csv", "Shutoko Battle Rival Manifest Master - Team Manifest SB(PSP).csv"),
    ("SBX", "07_SBX", "Shutoko Battle Rival Manifest Master - SBX.csv", "Shutoko Battle Rival Manifest Master - Team Manifest SBX.csv"),
    ("SB2025", "08_SB2025", "Shutoko Battle Rival Manifest Master - SB(2025).csv", "Shutoko Battle Rival Manifest Master - Team Manifest SB(2025).csv")
]

LANGS = ["CN", "EN", "ES", "RU"]

# ==============================================================================
# STAGE 3: STORY CUTSCENES (READY TO UNCOMMENT / ACTIVATE)
# ==============================================================================
def load_story_cutscenes():
    """
    Loads cutscene scripts and narrative milestones across games:
    - 02_SB0: story_shutoko_battle_zero_i18n.csv
    - 03_SB01: story_shutoko_battle_01_i18n.csv
    - 07_SBX: story_shutoko_battle_x.csv
    - 08_SB2025: story-stage*.csv
    """
    story_db = {}
    
# 1. SB0 & SB01 (Parallel multi-lingual sheets)
    for gid, gdir, fname in [
        ('SB0', '02_SB0', 'story_shutoko_battle_zero_i18n.csv'),
        ('SB01', '03_SB01', 'story_shutoko_battle_01_i18n.csv')
    ]:
        story_path = os.path.join(BASE_TR, 'JP', gdir, fname)
        if os.path.exists(story_path):
            lines = []
            with open(story_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                for row in csv.DictReader(f):
                    lines.append({
                        'stage': row.get('Stage', ''),
                        'sub': row.get('Subsection', ''),
                        'heading': row.get('Heading', ''),
                        'char': row.get('Character', ''),
                        'jp': row.get('Text_JP', ''),
                        'i18n': {
                            'EN': row.get('Text_EN', ''),
                            'ES': row.get('Text_ES', ''),
                            'RU': row.get('Text_RU', ''),
                            'CN': row.get('Text_CN', '')
                        }
                    })
            if lines:
                story_db[gid] = lines

    # 2. SBX & SB2025 across TR/<LANG>/
    for gid, gdir, story_pattern in [
        ('SBX', '07_SBX', 'story_shutoko_battle_x.csv'),
        ('SB2025', '08_SB2025', 'story-stage*.csv')
    ]:
        game_lines = []
        jp_dir = os.path.join(BASE_TR, 'JP', gdir)
        if os.path.exists(jp_dir):
            import glob
            files = sorted(glob.glob(os.path.join(jp_dir, story_pattern)))
            for fpath in files:
                fname = os.path.basename(fpath)
                with open(fpath, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    for row in csv.reader(f):
                        if len(row) >= 5 and row[0] not in ['Stage', 'Stage ID']:
                            game_lines.append({
                                'file': fname,
                                'stage': row[0],
                                'sub': row[1] if len(row) > 1 else '',
                                'heading': row[2] if len(row) > 2 else '',
                                'char': row[3] if len(row) > 3 else '',
                                'jp': row[4] if len(row) > 4 else '',
                                'i18n': {}
                            })
        # Check localized counterparts in TR/<LANG>/<gdir>/
        for lang in LANGS:
            lang_dir = os.path.join(BASE_TR, lang, gdir)
            if os.path.exists(lang_dir):
                import glob
                lfiles = sorted(glob.glob(os.path.join(lang_dir, story_pattern.replace('.csv', f'*{lang}*.csv') if '2025' in gdir else story_pattern)))
                if not lfiles:
                    lfiles = sorted(glob.glob(os.path.join(lang_dir, story_pattern)))
                idx = 0  # running index across files, mirrors JP concatenation
                for lf in lfiles:
                    with open(lf, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        for row in csv.reader(f):
                            # Same filter as the JP side so rows stay aligned (skips header)
                            if not (len(row) >= 5 and row[0] not in ['Stage', 'Stage ID']):
                                continue
                            if idx < len(game_lines):
                                # Text is typically the last column
                                text_trans = row[-1].strip()
                                if text_trans:
                                    game_lines[idx]['i18n'][lang] = text_trans
                            idx += 1
        if game_lines:
            story_db[gid] = game_lines

    return story_db


# ==============================================================================
# STAGE 4: PA DIALOGUES & TOUGE BBS (READY TO UNCOMMENT / ACTIVATE)
# ==============================================================================
def load_pa_dialogues():
    """
    Loads Parking Area chat logs & Touge BBS threads across games:
    - 07_SBX: pa_*.csv
    - 08_SB2025: pa_*.csv
    """
    pa_db = {}
    import glob
    for gid, gdir in [('SBX', '07_SBX'), ('SB2025', '08_SB2025')]:
        jp_dir = os.path.join(BASE_TR, 'JP', gdir)
        if not os.path.exists(jp_dir):
            continue
        pa_files = sorted(glob.glob(os.path.join(jp_dir, 'pa_*.csv')) + glob.glob(os.path.join(jp_dir, 'PA_*.csv')))
        def parse_pa_row(row):
            # SB2025: Stage,Namespace,Key,Battle ID,Situation Type,Situation,Line,R-Code,Character (JP),Character (xx),Text (JP),Text (xx)
            # SBX:    Stage,Subsection,Heading,Character,Text
            if not row or row[0].strip() in ('Stage', 'Stage ID', ''):
                return None
            if gid == 'SB2025':
                if len(row) < 11:
                    return None
                return {'sec': row[5], 'rcode': row[7].strip(), 'speaker': row[8], 'jp': row[10], 'i18n': {}}
            if len(row) < 5:
                return None
            return {'sec': row[2], 'rcode': '', 'speaker': row[3], 'jp': row[4], 'i18n': {}}
        for fpath in pa_files:
            area_key = os.path.splitext(os.path.basename(fpath))[0].lower().replace('-jp', '').replace('pa_', '')
            chat_entries = []
            with open(fpath, 'r', encoding='utf-8-sig', errors='ignore') as f:
                for row in csv.reader(f):
                    e = parse_pa_row(row)
                    if e:
                        chat_entries.append(e)
            # Localized versions in TR/<LANG>/<gdir>/
            for lang in LANGS:
                lang_dir = os.path.join(BASE_TR, lang, gdir)
                if not os.path.exists(lang_dir):
                    continue
                match = glob.glob(os.path.join(lang_dir, f"*{area_key}*.csv"))
                if match:
                    with open(match[0], 'r', encoding='utf-8-sig', errors='ignore') as f:
                        idx = 0
                        for row in csv.reader(f):
                            # Same filter as the JP side so rows stay aligned (skips header)
                            if not parse_pa_row(row):
                                continue
                            if idx < len(chat_entries):
                                trans_text = row[-1].strip()
                                if trans_text:
                                    chat_entries[idx]['i18n'][lang] = trans_text
                            idx += 1
            if chat_entries:
                pa_db.setdefault(gid, {})[area_key] = chat_entries

    return pa_db


def load_all_i18n():
    rival_i18n = {}
    team_bios_i18n = {}
    
    # Master Monikers
    monikers_master = {}
    mon_path = os.path.join(BASE_TR, 'master_monikers_i18n.csv')
    if os.path.exists(mon_path):
        with open(mon_path, 'r', encoding='utf-8', errors='ignore') as f:
            for row in csv.DictReader(f):
                gid = row.get('Game', '').strip()
                rcode = row.get('R_Code', '').strip()
                if gid and rcode:
                    monikers_master[(gid, rcode, 'EN')] = row.get('Moniker_EN', '').strip()
                    monikers_master[(gid, rcode, 'ES')] = row.get('Moniker_ES', '').strip()
                    monikers_master[(gid, rcode, 'RU')] = row.get('Moniker_RU', '').strip()

    # Master Persons
    persons_master = {}
    p_path = os.path.join(BASE_TR, 'master_persons_i18n.csv')
    if os.path.exists(p_path):
        with open(p_path, 'r', encoding='utf-8', errors='ignore') as f:
            for row in csv.DictReader(f):
                rname = row.get('RealName_JP', '').strip()
                if rname:
                    persons_master[(rname, 'EN')] = row.get('Name_EN', '').strip()
                    persons_master[(rname, 'ES')] = row.get('Name_ES', '').strip()
                    persons_master[(rname, 'RU')] = row.get('Name_RU', '').strip()
                    persons_master[(rname, 'CN')] = rname

    # Master Teams
    teams_master = {}
    t_path = os.path.join(BASE_TR, 'master_teams_i18n.csv')
    if os.path.exists(t_path):
        with open(t_path, 'r', encoding='utf-8', errors='ignore') as f:
            for row in csv.DictReader(f):
                tname = row.get('Team_Canonical', '').strip()
                if tname:
                    teams_master[(tname, 'EN')] = row.get('Team_EN', tname).strip()
                    teams_master[(tname, 'ES')] = row.get('Team_ES', tname).strip()
                    teams_master[(tname, 'RU')] = row.get('Team_RU', tname).strip()
                    teams_master[(tname, 'CN')] = tname

    # Manifests
    for gid, gdir, rfname, tfname in GAMES_META:
        for lang in LANGS:
            p_rival = os.path.join(BASE_TR, lang, gdir, rfname)
            if not os.path.exists(p_rival) and gid == "SB2025":
                p_rival = os.path.join(BASE_TR, lang, gdir, f"Shutoko Battle Rival Manifest Master - SB(2025) {lang}.csv")
            
            if os.path.exists(p_rival):
                with open(p_rival, 'r', encoding='utf-8', errors='ignore') as f:
                    for row in csv.DictReader(f):
                        rid = (row.get('R-Code') or row.get('ID') or row.get('\ufeffR-Code') or '').strip()
                        if not rid: continue
                        bio = (row.get('Bio') or row.get(f'Bio({lang})') or '').strip()
                        nick = (row.get('Nickname') or row.get('Nickname(Raw)') or '').strip()
                        real = (row.get('Real Name') or '').strip()
                        rel = (row.get('Relationships') or '').strip()
                        role = (row.get('Role') or '').strip()
                        
                        if not nick or (lang != 'CN' and any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in nick)):
                            if (gid, rid, lang) in monikers_master and monikers_master[(gid, rid, lang)]:
                                nick = monikers_master[(gid, rid, lang)]
                                
                        rival_i18n[(gid, rid, lang)] = {
                            'bio': bio,
                            'nick': nick,
                            'real': real,
                            'rel': rel,
                            'role': role
                        }

    # Multi-game Team Manifests
    team_manifest_sources = [
        (0, "SB1", "00_SB1", "Shutoko Battle Rival Manifest Master - Team Manifest SB(1999).csv"),
        (1, "SB2", "01_SB2", "Shutoko Battle Rival Manifest Master - Team Manifest SB2.csv"),
        (2, "SB0", "02_SB0", "Shutoko Battle Rival Manifest Master - Team Manifest SB0.csv"),
        (4, "SB01", "03_SB01", "Shutoko Battle Rival Manifest Master - Team Manifest SB01.csv"),
        (7, "PSP", "09_SB-PSP", "Shutoko Battle Rival Manifest Master - Team Manifest SB(PSP).csv"),
        (8, "SBX", "07_SBX", "Shutoko Battle Rival Manifest Master - Team Manifest SBX.csv"),
        (9, "SB2025", "08_SB2025", "Shutoko Battle Rival Manifest Master - Team Manifest SB(2025).csv")
    ]
    team_bios_by_game = {}

    for g_idx, gid, gdir, fname in team_manifest_sources:
        # 1. JP
        if gid == "SB2025":
            jp_path = r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\01_RIVALS\by_game\08_TXR25\Shutoko Battle Rival Manifest Master - Team Manifest SB(2025).csv'
        else:
            jp_path = os.path.join(BASE_TR, 'JP', gdir, fname)
            
        if os.path.exists(jp_path):
            with open(jp_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                for row in csv.reader(f):
                    if len(row) >= 2 and row[0].strip() and row[0].strip() not in ['Team Name', 'Team', 'Team(JP)']:
                        tname = row[0].strip()
                        _, tk = clean_team(tname)
                        bio_jp = row[1].strip()
                        team_bios_by_game.setdefault(tk, {}).setdefault(g_idx, {'jp': '', 'i18n': {}})['jp'] = bio_jp

        # 2. Localized
        for lang in LANGS:
            if gid == "SB2025":
                loc_path = os.path.join(BASE_TR, lang, gdir, f"Shutoko Battle Rival Manifest Master - Team Manifest SB(2025) {lang}.csv")
            else:
                loc_path = os.path.join(BASE_TR, lang, gdir, fname)
                
            if os.path.exists(loc_path):
                with open(loc_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    bio_col_idx = 1
                    if header:
                        for idx, c in enumerate(header):
                            if f'Bio({lang})' in c or 'Bio' in c:
                                bio_col_idx = idx
                    for row in reader:
                        if len(row) > bio_col_idx and row[0].strip() and row[0].strip() not in ['Team Name', 'Team', 'Team(JP)']:
                            tname = row[0].strip()
                            _, tk = clean_team(tname)
                            bio_loc = row[bio_col_idx].strip()
                            if bio_loc:
                                team_bios_by_game.setdefault(tk, {}).setdefault(g_idx, {'jp': '', 'i18n': {}})['i18n'][lang] = bio_loc

    return rival_i18n, team_bios_by_game, persons_master, monikers_master, teams_master


def build_multilingual_database():
    print("Loading name dictionaries and bios...")
    names = build_master_name_dict()
    en_bios = extract_all_en_bios()
    # MULTILINGUAL LOADER DISABLED (JP-only build). Re-enable by uncommenting the next line
    # and removing the empty defaults below.
    # rival_i18n, team_bios_by_game, persons_master, monikers_master, teams_master = load_all_i18n()
    rival_i18n, team_bios_by_game, persons_master, monikers_master, teams_master = {}, {}, {}, {}, {}
    
    records = []
    
    for g_idx, g_info in enumerate(GAMES):
        gid = g_info['id']
        path = g_info['path']
        print(f"Ingesting {gid} ({g_info['name']})...")
        
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rcode = (row.get('R-Code') or row.get('R_Code') or row.get('ID') or row.get('No.') or '').strip()
                if not rcode:
                    continue
                
                disp_raw = (row.get('Display Name') or '').strip()
                real_raw = (row.get('Real Name') or '').strip()
                nick_raw = clean_nick(row.get('Nickname') or '')
                role_raw = (row.get('Role') or 'Member').strip()
                team_raw = (row.get('Team Name') or row.get('Team') or '').strip()
                car_raw = (row.get('Chassis Code') or '').strip()
                plate_raw = (row.get('Plate') or '').strip()
                
                # Priority: Bio is the Japanese narrative rival bio. Notes contains metadata (Job/Area/Level).
                bio_raw = (row.get('Bio') or '').strip()
                notes_raw = (row.get('Notes') or '').strip()
                desc_raw = (row.get('Description') or '').strip()
                text_raw = bio_raw if bio_raw else (desc_raw or notes_raw)
                rel_raw = (row.get('Relationships') or '').strip()
                
                job = ''
                area = ''
                if notes_raw:
                    m_job = re.search(r'Job:\s*([^/]+)', notes_raw)
                    if m_job: job = m_job.group(1).strip()
                    m_area = re.search(r'Area:\s*([^/]+)', notes_raw)
                    if m_area: area = m_area.group(1).strip()
                
                disp, h_key = clean_handle(disp_raw)
                real = clean_real(real_raw)
                team, t_key = clean_team(team_raw)
                
                role = role_raw
                role_lower = role_raw.lower()
                if 'lead' in role_lower:
                    role = 'Leader'
                elif 'sub' in role_lower:
                    role = 'Sub-leader'
                elif 'last' in role_lower or 'boss' in role_lower:
                    role = 'Boss'
                elif 'wand' in role_lower or 'slasher' in role_lower:
                    role = 'Wanderer'
                else:
                    role = 'Member'
                
                spec = SPECIAL_ENTITIES.get((gid, rcode))
                if spec:
                    pkey = spec['pid']
                    canon_name = spec['name']
                    canon_nick = spec['nick']
                elif real:
                    pkey = f"n:{real}"
                    canon_name = real
                    canon_nick = nick_raw
                else:
                    pkey = f"h:{h_key}"
                    canon_name = disp
                    canon_nick = nick_raw
                    
                real_en = names.get(real, '') or names.get(real.replace(' ', ''), '')
                en_bio = en_bios.get((gid, rcode), '')
                
                # Assemble multilingual maps
                bio_i18n = {}
                nick_i18n = {}
                real_i18n = {}
                rel_i18n = {}
                role_i18n = {}
                
                for lang in LANGS:
                    info = rival_i18n.get((gid, rcode, lang), {})
                    b = info.get('bio', '').strip()
                    if lang == 'EN' and not b:
                        b = en_bio.strip()
                    if b:
                        bio_i18n[lang] = b
                        
                    n = info.get('nick', '').strip()
                    if not n and (gid, rcode, lang) in monikers_master:
                        n = monikers_master[(gid, rcode, lang)]
                    if lang == 'EN' and not n:
                        n = nick_raw
                    if n:
                        nick_i18n[lang] = n
                        
                    r_name = info.get('real', '').strip()
                    if not r_name and (real, lang) in persons_master:
                        r_name = persons_master[(real, lang)]
                    if lang == 'EN' and not r_name:
                        r_name = real_en
                    if r_name:
                        real_i18n[lang] = r_name
                        
                    rl = info.get('rel', '').strip()
                    if lang == 'EN' and not rl:
                        rl = rel_raw
                    if rl:
                        rel_i18n[lang] = rl
                        
                    ro = info.get('role', '').strip()
                    if ro:
                        role_i18n[lang] = ro

                records.append({
                    "g": g_idx,
                    "gid": gid,
                    "id": rcode,
                    "team": team,
                    "disp": disp,
                    "real": real,
                    "real_en": real_en,
                    "nick": nick_raw,
                    "role": role,
                    "car": car_raw,
                    "plate": plate_raw,
                    "text": text_raw,
                    "text_en": en_bio,
                    "notes": notes_raw,
                    "job": job,
                    "area": area,
                    "rel": rel_raw,
                    "pkey": pkey,
                    "canon_name": canon_name,
                    "canon_nick": canon_nick,
                    "tk": t_key,
                    "h_key": h_key,
                    "bio_i18n": bio_i18n,
                    "nick_i18n": nick_i18n,
                    "real_i18n": real_i18n,
                    "rel_i18n": rel_i18n,
                    "role_i18n": role_i18n
                })

    print(f"Total parsed records: {len(records)}")

    # Persons
    person_groups = defaultdict(list)
    for idx, r in enumerate(records):
        person_groups[r['pkey']].append(idx)

    # Load taxonomy (supports 1-3 pillars, 1-2 motivators)
    tax_map = {}
    tax_csv = r'p:\PROJECTS_ROOT\WIKI\TXR_Archive\zextras\chronicle_stuff\master_taxonomy.csv'
    if os.path.exists(tax_csv):
        with open(tax_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Support new Option A (pillar_1..3, motivator_1..2) with fallback to old column names
                p1 = row.get('pillar_1') or row.get('pillar', '')
                p2 = row.get('pillar_2', '')
                p3 = row.get('pillar_3', '')
                m1 = row.get('motivator_1') or row.get('motivator', '')
                m2 = row.get('motivator_2', '')
                pillars = [p.strip() for p in (p1, p2, p3) if p and p.strip()]
                motivators = [m.strip() for m in (m1, m2) if m and m.strip()]
                tax_map[(row.get('kind', '').strip().lower(), row.get('name', '').strip())] = {
                    'pillars': pillars or ['MARTIAL'],
                    'motivators': motivators or ['BOND']
                }

    persons = []
    pid_map = {}
    sorted_pkeys = sorted(person_groups.keys(), key=lambda k: (records[person_groups[k][0]]['g'], person_groups[k][0]))
    
    for p_num, pkey in enumerate(sorted_pkeys):
        p_id = f"p{p_num}"
        rec_indices = person_groups[pkey]
        first_r = records[rec_indices[0]]
        last_r = records[rec_indices[-1]]
        
        canon_name = first_r['canon_name']
        cleaned_nicks = [clean_nick(records[i]['nick']) for i in reversed(rec_indices) if clean_nick(records[i]['nick'])]
        canon_nick = Counter(cleaned_nicks).most_common(1)[0][0] if cleaned_nicks else (last_r['canon_nick'] or first_r['canon_nick'])
        disp_name = last_r['disp']
        
        games_attended = sorted(list(set(records[i]['g'] for i in rec_indices)))
        roles_held = sorted(list(set(records[i]['role'] for i in rec_indices)))
        
        themes = []
        if len(games_attended) >= 4:
            themes.append('long')
        elif len(games_attended) == 1:
            themes.append('once')
        
        if len(games_attended) > 1:
            for i in range(len(games_attended) - 1):
                if games_attended[i+1] - games_attended[i] > 1:
                    themes.append('returned')
                    break
        
        unique_disps = list(dict.fromkeys(records[i]['h_key'] for i in rec_indices))
        if len(unique_disps) > 1:
            themes.append('renamed')
        
        unique_teams = list(dict.fromkeys(records[i]['tk'] for i in rec_indices if records[i]['tk'] not in ['WANDERER', 'BOSS', 'SLASHER', '無所属', 'LASTBOSS', 'ZONEBOSS', 'MIDDLEBOSS', 'BIGBOSS']))
        if len(unique_teams) > 1:
            themes.append('moved')
        
        has_team = any(records[i]['tk'] not in ['WANDERER', 'BOSS', 'SLASHER', '無所属'] for i in rec_indices)
        has_wand = any(records[i]['tk'] in ['WANDERER', 'BOSS', 'SLASHER', '無所属'] for i in rec_indices)
        if has_team and has_wand:
            themes.append('drifted')
        
        spec_name_en = None
        for r_idx in rec_indices:
            r_item = records[r_idx]
            spec = SPECIAL_ENTITIES.get((r_item['gid'], r_item['id']))
            if spec and 'name_en' in spec:
                spec_name_en = spec['name_en']
                break
        canon_name_en = spec_name_en or names.get(canon_name, '') or names.get(canon_name.replace(' ', ''), canon_name)
        
        # Multilingual names for person
        name_i18n = {}
        nick_i18n = {}
        for lang in LANGS:
            if (canon_name, lang) in persons_master and persons_master[(canon_name, lang)]:
                name_i18n[lang] = persons_master[(canon_name, lang)]
            elif lang == 'EN':
                name_i18n[lang] = canon_name_en
            elif lang == 'CN':
                name_i18n[lang] = canon_name
                
            # Most common nickname in that language across records
            lang_nicks = [records[i]['nick_i18n'].get(lang, '') for i in reversed(rec_indices) if records[i]['nick_i18n'].get(lang, '')]
            if lang_nicks:
                nick_i18n[lang] = Counter(lang_nicks).most_common(1)[0][0]
            elif lang == 'EN':
                nick_i18n[lang] = canon_nick
                
        tax_entry = tax_map.get(('person', canon_name), {'pillars': ['MARTIAL'], 'motivators': ['BOND']})
        for p in tax_entry['pillars']:
            themes.append('p:' + p)
        for m in tax_entry['motivators']:
            themes.append('m:' + m)

        person_obj = {
            "id": p_id,
            "kind": "person",
            "name": canon_name,
            "name_en": canon_name_en,
            "name_i18n": name_i18n,
            "disp": disp_name,
            "nick": canon_nick,
            "nick_i18n": nick_i18n,
            "recs": rec_indices,
            "games": games_attended,
            "roles": roles_held,
            "themes": themes,
            "pillar": tax_entry['pillars'][0],
            "pillars": tax_entry['pillars'],
            "motivator": tax_entry['motivators'][0],
            "motivators": tax_entry['motivators'],
            "seats": []
        }
        persons.append(person_obj)
        pid_map[pkey] = p_id

    # Teams
    team_groups = defaultdict(list)
    for idx, r in enumerate(records):
        team_groups[r['tk']].append(idx)

    teams = []
    tid_map = {}
    sorted_tkeys = sorted(team_groups.keys(), key=lambda k: (records[team_groups[k][0]]['g'], team_groups[k][0]))
    for t_num, tk in enumerate(sorted_tkeys):
        t_id = f"t{t_num}"
        rec_indices = team_groups[tk]
        first_r = records[rec_indices[0]]
        
        team_name = first_r['team']
        alt_names = sorted(list(set(records[i]['team'] for i in rec_indices if records[i]['team'] != team_name)))
        games_attended = sorted(list(set(records[i]['g'] for i in rec_indices)))
        
        themes = []
        if len(games_attended) >= 5:
            themes.append('long')
        elif len(games_attended) == 1:
            themes.append('once')
        
        if len(games_attended) > 1:
            for i in range(len(games_attended) - 1):
                if games_attended[i+1] - games_attended[i] > 1:
                    themes.append('returned')
                    break
        
        leaders = []
        for i in rec_indices:
            r = records[i]
            if r['role'] == 'Leader':
                pid = pid_map[r['pkey']]
                if not leaders or leaders[-1] != pid:
                    leaders.append(pid)
        if len(leaders) > 1:
            themes.append('succession')
            
        if any(re.search(r'[0-9０-９一二三四五六七八九十]+号|No\.?\s*[0-9]+', records[i]['disp']) for i in rec_indices):
            themes.append('numbered')
            
        # Multilingual team names and multi-game bios
        t_name_i18n = {}
        for lang in LANGS:
            if (team_name, lang) in teams_master and teams_master[(team_name, lang)]:
                t_name_i18n[lang] = teams_master[(team_name, lang)]
                
        bios_list = []
        if tk in team_bios_by_game:
            for g_idx in sorted(team_bios_by_game[tk].keys()):
                b_data = team_bios_by_game[tk][g_idx]
                if b_data.get('jp') or any(b_data.get('i18n', {}).values()):
                    bios_list.append({
                        "g": g_idx,
                        "jp": b_data.get('jp', ''),
                        "i18n": b_data.get('i18n', {})
                    })
                
        # Bio25 or latest bio for backwards compatibility
        latest_en_bio = ''
        latest_jp_bio = ''
        if bios_list:
            latest_en_bio = bios_list[-1]['i18n'].get('EN', '')
            latest_jp_bio = bios_list[-1].get('jp', '')
                
        tax_entry = tax_map.get(('team', team_name), {'pillars': ['MARTIAL'], 'motivators': ['BOND']})
        for p in tax_entry['pillars']:
            themes.append('p:' + p)
        for m in tax_entry['motivators']:
            themes.append('m:' + m)

        teams.append({
            "id": t_id,
            "kind": "team",
            "name": team_name,
            "name_i18n": t_name_i18n,
            "alt": alt_names,
            "recs": rec_indices,
            "games": games_attended,
            "themes": themes,
            "pillar": tax_entry['pillars'][0],
            "pillars": tax_entry['pillars'],
            "motivator": tax_entry['motivators'][0],
            "motivators": tax_entry['motivators'],
            "bio25": latest_en_bio or latest_jp_bio,
            "bios": bios_list
        })
        tid_map[tk] = t_id

    # Connect pid and tid
    for r in records:
        r['pid'] = pid_map[r['pkey']]
        r['tid'] = tid_map[r['tk']]

    # Seats
    handle_holders = defaultdict(set)
    for r in records:
        handle_holders[r['h_key']].add(r['pid'])
        
    seats = {}
    for h_key, pids in handle_holders.items():
        if len(pids) > 1:
            sorted_pids = sorted(list(pids), key=lambda pid: persons[int(pid[1:])]['games'][0])
            seats[h_key] = sorted_pids
            for pid in sorted_pids:
                p_idx = int(pid[1:])
                if h_key not in persons[p_idx]['seats']:
                    persons[p_idx]['seats'].append(h_key)
                if 'sharedname' not in persons[p_idx]['themes']:
                    persons[p_idx]['themes'].append('sharedname')

    print(f"Total built: {len(persons)} persons, {len(teams)} teams, {len(seats)} seats.")

    return {
        "games": [{"id": g["id"], "year": g["year"], "name": g["name"]} for g in GAMES],
        "recs": [{
            "g": r["g"],
            "id": r["id"],
            "team": r["team"],
            "disp": r["disp"],
            "real": r["real"],
            "real_en": r.get("real_en", ""),
            "nick": r["nick"],
            "role": r["role"],
            "car": r["car"],
            "plate": r["plate"],
            "text": r["text"],
            "text_en": r.get("text_en", ""),
            "notes": r.get("notes", ""),
            "job": r.get("job", ""),
            "area": r.get("area", ""),
            "rel": r["rel"],
            "pkey": r["pkey"],
            "pid": r["pid"],
            "tid": r["tid"],
            "tk": r["tk"],
            "bio_i18n": r["bio_i18n"],
            "nick_i18n": r["nick_i18n"],
            "real_i18n": r["real_i18n"],
            "rel_i18n": r["rel_i18n"],
            "role_i18n": r["role_i18n"]
        } for r in records],
        "persons": persons,
        "teams": teams,
        "seats": seats
    }

if __name__ == '__main__':
    db = build_multilingual_database()
    db_json = json.dumps(db, ensure_ascii=False, separators=(',', ':'))
    print(f"Compiled multilingual database JSON length: {len(db_json):,} characters.")
    
    # Check sample record
    r0 = db['recs'][0]
    print("Sample rec 0:", {k: r0[k] for k in ['id', 'disp', 'real', 'nick', 'bio_i18n', 'nick_i18n', 'real_i18n', 'rel_i18n']})
