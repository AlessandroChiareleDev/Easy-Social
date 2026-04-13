import pathlib

p = pathlib.Path("/opt/easy-social/python-scripts/excluir_s1210_ativo.py")
txt = p.read_text()

old = 'GRUPO = 3  # S-3000 vai no mesmo grupo do evento-alvo (S-1210 = periodico = grupo 3)'
new = 'GRUPO = 2  # S-3000 sempre vai no grupo 2 (Nao Periodicos) - evento de exclusao'

assert old in txt, "Old text not found!"
txt = txt.replace(old, new, 1)
p.write_text(txt)
print("GRUPO changed to 2!")
