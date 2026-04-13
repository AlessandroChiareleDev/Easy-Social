import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esocial.xml_s3000 import S3000XMLGenerator

empregador = {"tpInsc": "1", "nrInsc": "05969071000110"}
xml = S3000XMLGenerator.gerar(
    empregador=empregador,
    tp_evento="S-1210",
    nr_rec_evt="1.1.0000000035299436298",
    cpf_trab="31381951805",
    per_apur="2025-09",
    ind_apuracao="1",
    tp_amb="1",
)
print(xml.decode())
