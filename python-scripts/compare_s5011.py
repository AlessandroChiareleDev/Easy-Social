import os, glob, xml.etree.ElementTree as ET, json

s5011_dir = r'C:\Users\xandao\Downloads\29076329'
files = sorted(glob.glob(os.path.join(s5011_dir, '*.S-5011.xml')))

print(f'Files in {os.path.basename(s5011_dir)}:')
for f in files:
    print(f'  {os.path.basename(f)}')

def parse_s5011(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    result = {'periodo': None, 'lotacoes': [], 'crs': []}
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'perApur':
            result['periodo'] = elem.text
        elif tag == 'indApuracao':
            result['indApuracao'] = elem.text
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'ideLotacao':
            lot = {}
            bases_list = []
            current_base = None
            for child in elem.iter():
                ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if ctag == 'ideLotacao':
                    continue
                elif ctag in ('codLotacao', 'fpas', 'codTercs', 'codTercSusp'):
                    lot[ctag] = child.text
                elif ctag == 'basesRemun':
                    current_base = {}
                    bases_list.append(current_base)
                elif current_base is not None and ctag not in ('basesRemun',):
                    if child.text:
                        current_base[ctag] = child.text
            lot['bases'] = bases_list
            result['lotacoes'].append(lot)
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'infoCREstab':
            cr = {}
            for child in elem:
                ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                cr[ctag] = child.text
            result['crs'].append(cr)
    return result

parsed = {}
for f in files:
    bn = os.path.basename(f)
    data = parse_s5011(f)
    has_e = any(l.get('codLotacao', '').startswith('E') for l in data['lotacoes'])
    key = f"{data['periodo']}_{'COM_E' if has_e else 'SEM_E'}_{bn[:20]}"
    parsed[key] = data
    print(f'\n{key}: {len(data["lotacoes"])} lotacoes, {len(data["crs"])} CRs')

periods = {}
for key, data in parsed.items():
    per = data['periodo']
    has_e = 'COM_E' in key
    if per not in periods:
        periods[per] = {'com_e': [], 'sem_e': []}
    if has_e:
        periods[per]['com_e'].append((key, data))
    else:
        periods[per]['sem_e'].append((key, data))

print('\n\n========== COMPARISON ==========')
for per, pair in periods.items():
    if pair['com_e'] and pair['sem_e']:
        print(f'\n*** Periodo {per} - TEM PAR COM/SEM E ***')
        sem_key, sem_data = pair['sem_e'][0]
        com_key, com_data = pair['com_e'][0]
        sem_lots = {}
        for l in sem_data['lotacoes']:
            code = l.get('codLotacao', '')
            sem_lots[code] = l
        com_lots = {}
        for l in com_data['lotacoes']:
            code = l.get('codLotacao', '')
            base_code = code[1:] if code.startswith('E') else code
            com_lots[base_code] = l
        common = set(sem_lots.keys()) & set(com_lots.keys())
        only_sem = set(sem_lots.keys()) - set(com_lots.keys())
        only_com = set(com_lots.keys()) - set(sem_lots.keys())
        print(f'  SEM E: {len(sem_lots)} lotacoes')
        print(f'  COM E: {len(com_lots)} lotacoes')
        print(f'  Em comum (by base code): {len(common)}')
        print(f'  So em SEM_E: {len(only_sem)} -> {sorted(only_sem)[:5]}')
        print(f'  So em COM_E: {len(only_com)} -> {sorted(only_com)[:5]}')
        for code in sorted(common)[:3]:
            sem = sem_lots[code]
            com = com_lots[code]
            print(f'\n  --- Lotacao {code} ---')
            print(f'    SEM_E: codLot={sem["codLotacao"]} fpas={sem.get("fpas")} codTercs={sem.get("codTercs")}')
            print(f'    COM_E: codLot={com["codLotacao"]} fpas={com.get("fpas")} codTercs={com.get("codTercs")}')
            for i, (sb, cb) in enumerate(zip(sem.get('bases', []), com.get('bases', []))):
                diffs = {}
                all_keys = set(sb.keys()) | set(cb.keys())
                for k in sorted(all_keys):
                    sv = sb.get(k, 'N/A')
                    cv = cb.get(k, 'N/A')
                    if sv != cv:
                        diffs[k] = (sv, cv)
                if diffs:
                    print(f'    Base[{i}] DIFFS:')
                    for k, (sv, cv) in diffs.items():
                        print(f'      {k}: SEM={sv} -> COM={cv}')
                else:
                    print(f'    Base[{i}]: IDENTICAL')
        sem_crs = {cr.get('tpCR',''): cr.get('vrCR','') for cr in sem_data['crs']}
        com_crs = {cr.get('tpCR',''): cr.get('vrCR','') for cr in com_data['crs']}
        print(f'\n  --- CRs ---')
        print(f'    SEM_E: {len(sem_crs)} CRs')
        print(f'    COM_E: {len(com_crs)} CRs')
        all_cr_keys = sorted(set(sem_crs.keys()) | set(com_crs.keys()))
        for cr_key in all_cr_keys:
            sv = sem_crs.get(cr_key, 'N/A')
            cv = com_crs.get(cr_key, 'N/A')
            marker = ' ***' if sv != cv else ''
            print(f'    tpCR {cr_key}: SEM={sv} COM={cv}{marker}')
    elif pair['com_e'] and not pair['sem_e']:
        print(f'\nPeriodo {per}: so COM E ({len(pair["com_e"])} arquivos)')
    elif pair['sem_e'] and not pair['com_e']:
        print(f'\nPeriodo {per}: so SEM E ({len(pair["sem_e"])} arquivos)')

print('\n\n========== TOP SUSPENSIONS (COM E) ==========')
for key, data in parsed.items():
    if 'COM_E' not in key:
        continue
    print(f'\n{key} (per={data["periodo"]}):')
    susp_lots = []
    for l in data['lotacoes']:
        for b in l.get('bases', []):
            vr = float(b.get('vrSuspBcCp00', '0'))
            if vr > 0:
                susp_lots.append((vr, l['codLotacao'], b.get('codCateg', '?'), b))
    susp_lots.sort(reverse=True)
    for vr, code, cat, b in susp_lots[:5]:
        print(f'  {code} cat={cat} vrSuspBcCp00={vr}')
        print(f'    vrBcCp00={b.get("vrBcCp00")} vrSuspBcCp00={b.get("vrSuspBcCp00")} vrSuspBcCp15={b.get("vrSuspBcCp15","0")} vrSuspBcCp20={b.get("vrSuspBcCp20","0")}')
