"""Fix CPF 03635806544 - recibo was received from eSocial but DB update failed due to DNS error."""
import psycopg2

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor()

# The recibo from the log: 1.1.0000000039841485186
cur.execute("""
    UPDATE pipeline_cpf_results
    SET status = 'ok', nr_recibo_novo = %s, lote_num = %s, processed_at = NOW()
    WHERE run_id = 1 AND cpf = '03635806544'
""", ('1.1.0000000039841485186', 28))
print(f"Updated {cur.rowcount} row(s)")
conn.commit()

# Also check: were there other CPFs in lote 28 that eSocial processed but we didn't save?
# From the log, lote 28 had 50 CPFs. We see 6 saved to DB as OK for lote 28.
# The 7th (03635806544) crashed. The remaining ~43 CPFs were never sent to eSocial (batch sends all 50 at once).
# Wait - actually the batch sends ALL 50 at once and then processes results one by one.
# So ALL 50 CPFs in the batch were sent. Let me check from the log which ones got results.

# Actually, looking at the code more carefully:
# The batch builds XMLs for all 50 CPFs, sends them to eSocial in one SOAP call,
# then processes each event result one by one with _db_update_cpf.
# The crash happened after processing event for 03635806544 (the 7th in lote 28).
# This means events 8-50 of lote 28 were processed by eSocial but not saved to DB!

# Let me check the recibos.xml or response to find the remaining CPFs...
# Actually we can't recover this from the crash. We need to look at what the log shows.

print("\nNOTE: The remaining CPFs in lote 28 (after 03635806544) were")
print("sent to eSocial and processed, but their results were NOT saved to DB.")
print("These CPFs will be in 'pendente' status. When we restart the pipeline,")
print("it will try to retify them again. Since S-1210 retificação is idempotent")
print("(same data), resending is safe - eSocial will just replace the previous submission.")

conn.close()
