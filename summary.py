import json

def load_data():
    res_path = r"relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/resolvedor_quinzenais_dtpgto_agosto_202_deddepen.json"
    pre_path = r"relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/preflight_agosto_202_deddepen.json"
    
    with open(res_path, "r", encoding="utf-8") as f:
        res_data = json.load(f)
    with open(pre_path, "r", encoding="utf-8") as f:
        pre_data = json.load(f)
    return res_data, pre_data

res, pre = load_data()

# Preflight targets are in 'evidence' key
pre_list = pre.get("evidence", [])
total_aug_targets = len(pre_list)
with_orig_xml = [r for r in pre_list if r.get("original_xml_zip") and r.get("original_xml_entry")]

# Resolver results are in 'records' key
res_list = res.get("records", [])

status_counts = {}
both_adj = []
any_adj = []
real_dep_adj = []
zero_totalizer_adj = []
real_cpfs_aug = []

for r in res_list:
    st = r.get("status", "unknown")
    status_counts[st] = status_counts.get(st, 0) + 1
    
    cpf = r.get("cpf")
    provas = r.get("provas", {})
    j_ev = provas.get("07")
    s_ev = provas.get("09")
    
    has_july = bool(j_ev)
    has_sept = bool(s_ev)
    
    if has_july or has_sept:
        any_adj.append(cpf)
    if has_july and has_sept:
        both_adj.append(cpf)
        
    # Real dependents in adjacent months
    found_dep = False
    for m_ev in [j_ev, s_ev]:
        if m_ev and isinstance(m_ev, dict):
            # Check 'dependentes' list
            deps = m_ev.get("dependentes", [])
            if any(d.get("cpf") for d in deps if isinstance(d, dict)):
                found_dep = True
                break
    if found_dep:
        real_dep_adj.append(cpf)
        
    # Zero totalizer checking - depends on 'total' or 'valor' fields
    # Assuming if a month event exists but has no real deps or total is 0
    # For now, let's use presence of 'totalizer' key or similar
    def is_zero(ev):
        if not ev: return False
        return ev.get("total_deducao", 1) == 0 # assuming field name
        
    if (has_july and is_zero(j_ev)) or (has_sept and is_zero(s_ev)):
        zero_totalizer_adj.append(cpf)

for r in pre_list:
    deps = r.get("dependentes", []) or r.get("dependents", [])
    if any(d.get("cpf") for d in deps if isinstance(d, dict)):
        real_cpfs_aug.append(r.get("cpf"))

print(f"Total August 202 targets: {total_aug_targets}")
print(f"Records with orig August XML zip+entry: {len(with_orig_xml)}")
print(f"Status counts: {status_counts}")
print(f"Records with both July and September adjacent: {len(both_adj)}")
print(f"Records with any adjacent events: {len(any_adj)}")
print(f"Records with real dependent CPFs in adjacent months: {len(real_dep_adj)}")
print(f"Records with only zero totalizer in adjacent months: {len(zero_totalizer_adj)}")
print(f"Records with real CPFs in August target: {len(real_cpfs_aug)}")

def sample(lst):
    return [x for x in lst if x][:5]

print(f"Sample Both Adj: {sample(both_adj)}")
print(f"Sample Real Dep Adj: {sample(real_dep_adj)}")
