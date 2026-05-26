import os
import json
import psycopg2
from psycopg2 import extras
from datetime import datetime

def run_analysis():
    conn_str_local = "dbname=easy_social_solucoes user=postgres password=postgres host=localhost"
    conn_str_remote = "postgresql://postgres:EsoV2_CoxRHWQ1z6iucG7ZyvdqFIbN@db.kjbgiwnlvqnrfdozjvhq.supabase.co:5432/postgres?sslmode=require"
    
    conn = None
    try:
        conn = psycopg2.connect(conn_str_local)
    except Exception:
        try:
            conn = psycopg2.connect(conn_str_remote)
        except Exception as e2:
            print(f"Connection failed: {e2}")
            return

    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("SET search_path TO solucoes, public")
        
        # Check column names
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'solucoes' AND table_name = 'timeline_envio'")
        cols = [r['column_name'] for r in cur.fetchall()]
        print(f"Columns in timeline_envio: {cols}")
        cpf_col = 'cpf' if 'cpf' in cols else 'identifier' # fallback just in case
        
        cur.execute("SELECT DISTINCT per_apur FROM timeline_mes ORDER BY per_apur DESC")
        months = [r['per_apur'] for r in cur.fetchall()]
        
        report_data = []
        for month in months:
            # 1. Distinct HEAD S-1210 CPFs
            cur.execute(f"SELECT count(distinct cpf) as count FROM explorador_eventos WHERE per_apur = %s AND retificado_por_id IS NULL AND tipo_evento = 'S-1210'", (month,))
            head_cpfs = cur.fetchone()['count']
            
            # 2. Distinct CPFs with any timeline item
            cur.execute(f"SELECT count(distinct te.{cpf_col}) as count FROM timeline_envio te JOIN timeline_mes tm ON te.timeline_mes_id = tm.id WHERE tm.per_apur = %s", (month,))
            timeline_cpfs = cur.fetchone()['count']
            
            # 3. Latest status per cpf and counts
            cur.execute(f"""
                WITH latest_items AS (
                    SELECT DISTINCT ON (te.{cpf_col}) 
                        te.{cpf_col} as cpf, 
                        tei.status, 
                        tei.erro_codigo,
                        tei.erro_esocial
                    FROM timeline_envio te
                    JOIN timeline_mes tm ON te.timeline_mes_id = tm.id
                    JOIN timeline_envio_item tei ON tei.timeline_envio_id = te.id
                    WHERE tm.per_apur = %s
                    ORDER BY te.{cpf_col}, tei.criado_em DESC, tei.id DESC
                )
                SELECT 
                    status,
                    count(*) as total,
                    count(*) FILTER (WHERE erro_codigo = '202' OR (erro_esocial ILIKE '%%202%%' AND status = 'erro_esocial')) as count_202,
                    count(*) FILTER (WHERE status = 'erro_esocial' AND NOT (erro_codigo = '202' OR erro_esocial ILIKE '%%202%%')) as real_errors,
                    count(*) FILTER (WHERE status IN ('pendente', 'pendente_consulta')) as pending
                FROM latest_items
                GROUP BY status
            """, (month,))
            status_stats = cur.fetchall()
            
            # 4. Error breakdown
            cur.execute(f"""
                WITH latest_items AS (
                    SELECT DISTINCT ON (te.{cpf_col}) 
                        tei.erro_codigo,
                        tei.erro_esocial
                    FROM timeline_envio te
                    JOIN timeline_mes tm ON te.timeline_mes_id = tm.id
                    JOIN timeline_envio_item tei ON tei.timeline_envio_id = te.id
                    WHERE tm.per_apur = %s AND tei.status = 'erro_esocial'
                    ORDER BY te.{cpf_col}, tei.criado_em DESC, tei.id DESC
                )
                SELECT erro_codigo, count(*) as count
                FROM latest_items
                WHERE NOT (erro_codigo = '202' OR erro_esocial ILIKE '%%202%%')
                GROUP BY erro_codigo
            """, (month,))
            error_breakdown = cur.fetchall()
            
            report_data.append({
                "per_apur": month,
                "head_s1210_cpfs": head_cpfs,
                "timeline_cpfs": timeline_cpfs,
                "status_stats": status_stats,
                "error_breakdown": error_breakdown
            })
            
        cur.execute("SELECT count(*) as count FROM timeline_envio_item WHERE status = 'erro_esocial' AND (erro_codigo = '202' OR erro_esocial ILIKE '%%202%%') LIMIT 1")
        is_202_error = cur.fetchone()['count'] > 0
        
        final_report = {
            "is_202_stored_as_erro_esocial": is_202_error,
            "data": report_data,
            "generated_at": datetime.now().isoformat()
        }
        
        os.makedirs("relatorio_ana", exist_ok=True)
        with open("relatorio_ana/LEVANTAMENTO_SOLUCOES_ERROS_PENDENTES_202_COMO_SUCESSO.json", "w") as f:
            json.dump(final_report, f, indent=4)
            
        print("\nSUMMARY TABLE:")
        print(f"{'Month':<10} | {'S1210 Head':<10} | {'TL CPFs':<10} | {'Success*':<10} | {'Real Err':<10} | {'Pending':<10}")
        print("-" * 75)
        for d in report_data:
            success_plus_202, real_err, pending = 0, 0, 0
            for s in d['status_stats']:
                if s['status'] == 'sucesso': success_plus_202 += s['total']
                if s['status'] == 'erro_esocial':
                    success_plus_202 += s['count_202']
                    real_err += s['real_errors']
                if s['status'] in ['pendente', 'pendente_consulta']:
                    pending += s['total']
            print(f"{d['per_apur']:<10} | {d['head_s1210_cpfs']:<10} | {d['timeline_cpfs']:<10} | {success_plus_202:<10} | {real_err:<10} | {pending:<10}")
            
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_analysis()
