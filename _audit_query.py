from app import db
EMP=2
with db.cursor(empresa_id=EMP) as cur:
    cur.execute("""
        select id,status,total_tentados,total_sucesso,total_erro,resumo
          from timeline_envio
         where id >= 585
         order by id
    """)
    print('ENVIOS', [dict(r) for r in cur.fetchall()])
    cur.execute("""
        select timeline_envio_id,status,erro_codigo,count(*) as n
          from timeline_envio_item
         where timeline_envio_id >= 585
         group by timeline_envio_id,status,erro_codigo
         order by timeline_envio_id,status,erro_codigo
    """)
    print('ITEMS', [dict(r) for r in cur.fetchall()])
