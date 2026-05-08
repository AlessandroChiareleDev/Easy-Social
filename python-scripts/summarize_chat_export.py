"""Summarize a VS Code Copilot chat export (chat.json) using streaming parser."""
import os, json, sys, io
from ijson.backends import python as ijson
from pathlib import Path

src = Path(os.path.expanduser("~/Downloads/chat.json"))
out_dir = Path(__file__).parent / "_chat_export_summary"
out_dir.mkdir(exist_ok=True)

print(f"Lendo: {src} ({src.stat().st_size/1024/1024:.1f} MB)")

requests = []
with open(src, "rb") as raw:
    f = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
    for req in ijson.items(f, "requests.item"):
        user_text = ""
        msg = req.get("message") or {}
        user_text = msg.get("text", "") or ""
        # response: pode ser lista de objetos com 'value' ou 'text'
        resp = req.get("response") or []
        resp_text_parts = []
        if isinstance(resp, list):
            for r in resp:
                if isinstance(r, dict):
                    v = r.get("value") or r.get("text") or ""
                    if isinstance(v, str):
                        resp_text_parts.append(v)
        resp_text = "\n".join(resp_text_parts)
        requests.append({
            "requestId": req.get("requestId"),
            "timestamp": req.get("timestamp"),
            "user": user_text,
            "user_len": len(user_text),
            "resp_len": len(resp_text),
            "resp_preview": resp_text[:300],
        })

print(f"Total de requests: {len(requests)}")

# Salva resumo compacto
summary_path = out_dir / "summary.json"
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump([
        {k: v for k, v in r.items() if k != "resp_preview"} | {"resp_preview": r["resp_preview"]}
        for r in requests
    ], f, ensure_ascii=False, indent=2)
print(f"Resumo salvo em: {summary_path}")

# Texto legível
txt_path = out_dir / "user_messages.txt"
with open(txt_path, "w", encoding="utf-8") as f:
    for i, r in enumerate(requests, 1):
        f.write(f"\n===== [{i}] {r.get('timestamp','')} =====\n")
        f.write(r["user"] + "\n")
print(f"Mensagens do usuário em: {txt_path}")

# Mostrar primeiras mensagens
print("\n--- Primeiras 5 mensagens do usuário ---")
for i, r in enumerate(requests[:5], 1):
    snippet = r["user"][:200].replace("\n", " ")
    print(f"[{i}] {snippet}")
