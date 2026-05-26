import zipfile
import os
import collections

dir_path = r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES"
tokens_to_count = ["cpfDep", "dedDepen", "vlrDedDep", "tpDep", "infoDep", "depIRRF", "valor unit", "unitario", "unitário"]
snippet_tokens = ["cpfDep", "dedDepen", "vlrDedDep"]

counts = collections.Counter()
snippets = []

if not os.path.exists(dir_path):
    print(f"Directory not found: {dir_path}")
    exit()

zips = [f for f in os.listdir(dir_path) if f.lower().endswith(".zip")]

for zip_name in zips:
    zip_path = os.path.join(dir_path, zip_name)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for entry_name in z.namelist():
                if not entry_name.lower().endswith(".xml"):
                    continue
                try:
                    with z.open(entry_name) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                        
                        # Count tokens
                        for token in tokens_to_count:
                            counts[token] += content.count(token)
                        
                        # Collect snippets
                        if len(snippets) < 10:
                            found_in_entry = False
                            for token in snippet_tokens:
                                if token in content:
                                    idx = content.find(token)
                                    start = max(0, idx - 50)
                                    end = min(len(content), idx + 250)
                                    snip = content[start:end].replace("\n", " ").strip()
                                    snippets.append((zip_name, entry_name, snip))
                                    found_in_entry = True
                                    break
                except Exception:
                    pass
    except Exception:
        pass

print("Token Counts:")
for token in tokens_to_count:
    print(f"  {token}: {counts[token]}")

print("\nSnippets (Found in cpfDep, dedDepen, vlrDedDep):")
for zip_n, entry_n, snip in snippets:
    print(f"Zip: {zip_n} | Entry: {entry_n}")
    print(f"  Snippet: {snip}...")
    print("-" * 20)
