"""
Migração: Preenche colunas col_k até col_bb a partir do raw_data JSONB existente.
Executa após o backend criar as novas colunas.
"""
import psycopg2
import json

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "easy_social_db",
    "user": "easy_social_user",
    "password": "sua_senha_segura",
}

TABLES = ["analise_natureza", "dinamica", "tabela_eventos_gl", "tabela_eb"]

def col_name_for_index(i: int) -> str:
    """0→col_a, 25→col_z, 26→col_aa, 53→col_bb"""
    letter = ""
    num = i
    while num >= 0:
        letter = chr(97 + (num % 26)) + letter
        num = num // 26 - 1
    return f"col_{letter}"

def excel_col_letter(i: int) -> str:
    """0→A, 25→Z, 26→AA, 53→BB"""
    letter = ""
    num = i
    while num >= 0:
        letter = chr(65 + (num % 26)) + letter
        num = num // 26 - 1
    return letter

def migrate_table(cur, table_name):
    # Get all rows with raw_data
    cur.execute(f"SELECT id, raw_data FROM {table_name} WHERE raw_data IS NOT NULL")
    rows = cur.fetchall()
    
    if not rows:
        print(f"  ⚠️  {table_name}: nenhuma linha com raw_data")
        return
    
    # Check how many keys the first row has to determine column count
    sample = rows[0][1] if isinstance(rows[0][1], dict) else json.loads(rows[0][1])
    max_keys = max(len(r[1] if isinstance(r[1], dict) else json.loads(r[1])) for r in rows)
    print(f"  📊 {table_name}: {len(rows)} linhas, até {max_keys} colunas no raw_data")
    
    if max_keys <= 10:
        print(f"  ✅ {table_name}: já coberto por col_a a col_j, nada a migrar")
        return
    
    # For columns 10+ (col_k onwards), extract from raw_data and update
    updated = 0
    batch_size = 200
    
    for batch_start in range(0, len(rows), batch_size):
        batch = rows[batch_start:batch_start + batch_size]
        
        for row_id, raw in batch:
            data = raw if isinstance(raw, dict) else json.loads(raw)
            keys = list(data.keys())
            
            if len(keys) <= 10:
                continue
            
            # Build SET clause for columns 10+
            set_parts = []
            values = []
            
            for i in range(10, min(54, len(keys))):
                db_col = col_name_for_index(i)
                # Try Excel letter first, then positional key
                excel_letter = excel_col_letter(i)
                value = data.get(excel_letter)
                if value is None and i < len(keys):
                    value = data.get(keys[i])
                
                if value is not None:
                    set_parts.append(f"{db_col} = %s")
                    values.append(str(value))
            
            if set_parts:
                values.append(row_id)
                cur.execute(
                    f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE id = %s",
                    values
                )
                updated += 1
        
        if len(rows) > batch_size:
            print(f"  ⏳ {table_name}: {min(batch_start + batch_size, len(rows))}/{len(rows)} linhas processadas")
    
    print(f"  ✅ {table_name}: {updated} linhas atualizadas com colunas extras")

def main():
    print("🔄 Iniciando migração de colunas (col_k até col_bb)...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        for table in TABLES:
            print(f"\n📋 Migrando {table}...")
            migrate_table(cur, table)
        
        conn.commit()
        print("\n✅ Migração concluída com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro na migração: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
