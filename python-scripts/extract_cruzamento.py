"""
Extrai dados do cruzamento EB Skills a partir dos arquivos de snapshot do browser.
Combina parte 1 e parte 2 e salva em tabela_eb_cruzamento.json
"""
import json
import re
import sys

PART1_PATH = r'c:\Users\xandao\AppData\Roaming\Code\User\workspaceStorage\288fd1ecc6d3eb74af7b338cebd535fb\GitHub.copilot-chat\chat-session-resources\eeaed927-ee7b-4480-af22-7d2fe40bd1f6\toolu_vrtx_01YK5nX6fvaFd39oRag7f6Tx__vscode-1774660093496\content.json'
PART2_PATH = r'c:\Users\xandao\AppData\Roaming\Code\User\workspaceStorage\288fd1ecc6d3eb74af7b338cebd535fb\GitHub.copilot-chat\chat-session-resources\eeaed927-ee7b-4480-af22-7d2fe40bd1f6\toolu_vrtx_01SuCQkC92p1pcWk7gvWiqpN__vscode-1774660093497\content.json'
OUTPUT_PATH = r'c:\Users\xandao\Documents\GitHub\Easy-Social\python-scripts\tabela_eb_cruzamento.json'


def extract_part(file_path, key):
    with open(file_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    text = raw['content'][0]['text']
    match = re.search(r'### Result\n(.*?)\n### Ran', text, re.DOTALL)
    if not match:
        print(f'Could not find Result in {file_path}')
        return []
    raw_json = match.group(1).strip()
    # The result may be double-encoded (JSON string inside JSON string)
    parsed = json.loads(raw_json)
    if isinstance(parsed, str):
        parsed = json.loads(parsed)
    return parsed.get(key, [])


def main():
    part1 = extract_part(PART1_PATH, 'part1')
    print(f'Part 1: {len(part1)} rows')

    part2 = extract_part(PART2_PATH, 'part2')
    print(f'Part 2: {len(part2)} rows')

    all_data = part1 + part2
    print(f'Total combined: {len(all_data)} rows')

    # Remove the status column - it will be computed in the frontend
    for row in all_data:
        row.pop('status', None)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f'Saved to {OUTPUT_PATH}')

    # Show samples
    print('\n--- Primeiras 3 rubricas ---')
    for row in all_data[:3]:
        print(f"  ID={row['idRub']}, {row['rubrica'][:35]}")
        print(f"    Sistema: INSS={row['incidINSS']}, IRRF={row['incidIRRF']}, FGTS={row['incidFGTS']}")
        print(f"    Correto: {row['incidBaseLegalINSS'][:40]}")
        print(f"             {row['incidBaseLegalIRRF'][:40]}")
        print(f"             {row['incidBaseLegalFGTS'][:40]}")

    # Count inconsistencies (where current != correct code)
    inconsistencias = 0
    for row in all_data:
        inss_code = row['incidBaseLegalINSS'].split(' - ')[0].strip() if row['incidBaseLegalINSS'] else ''
        irrf_code = row['incidBaseLegalIRRF'].split(' - ')[0].strip() if row['incidBaseLegalIRRF'] else ''
        fgts_code = row['incidBaseLegalFGTS'].split(' - ')[0].strip() if row['incidBaseLegalFGTS'] else ''
        if (row['incidINSS'] != inss_code or
            row['incidIRRF'] != irrf_code or
            row['incidFGTS'] != fgts_code):
            inconsistencias += 1

    print(f'\nInconsistências detectadas: {inconsistencias} de {len(all_data)}')
    print(f'Regulares: {len(all_data) - inconsistencias}')


if __name__ == '__main__':
    main()
