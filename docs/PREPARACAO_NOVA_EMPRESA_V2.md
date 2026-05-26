# Preparacao para Nova Empresa no Easy-eSocial V2

Documento de prontidao para receber uma terceira empresa no mesmo padrao usado na SOLUCOES: certificado A1, senha e 12 ZIPs mensais do eSocial.

## Estado verificado em 2026-05-20

- O V2 ativo esta em `C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2`.
- O backend e FastAPI e fica em `backend/app`.
- O frontend e Vue/Pinia/Vite e fica em `src`.
- Ha dois niveis de banco:
  - Sistema DB: autenticacao, usuarios, empresas e permissoes.
  - Dados DB: dados operacionais, isolados por schema PostgreSQL.
- Empresas ativas hoje:
  - APPA: CNPJ `05969071000110`, schema `appa`, versao `1.1.0`.
  - SOLUCOES: CNPJ `09445502000109`, schema `solucoes`, versao `1.1.0`.
- A usuaria Ana esta vinculada como `operador` nas duas empresas. O super_admin enxerga todas por override.
- Schemas `appa` e `solucoes` tem migrations `empresa` versoes `1.0.0` e `1.1.0` aplicadas.
- Volumes verificados:
  - `appa.explorador_eventos`: 375.985 linhas; `certificados_a1`: 1.
  - `solucoes.empresa_zips_brutos`: 24 ZIPs; `explorador_eventos`: 2.636.102 linhas; `timeline_mes`: 12; `timeline_envio`: 1.236; `timeline_envio_item`: 191.858.

## Modelo que deve ser repetido

1. Cada empresa entra em `sistema.empresas_routing` com CNPJ, razao social, `schema_name`, versao e ativo.
2. Cada usuario autorizado entra em `sistema.user_empresas` com papel (`admin`, `operador` ou `leitor`).
3. O schema da empresa no Dados DB recebe as migrations `empresa_v1.0.0` e `empresa_v1.1.0`.
4. Os ZIPs originais sao preservados em `empresa_zips_brutos` como Large Object, com hash, tamanho, periodo e status de extracao.
5. Cada XML dentro do ZIP vira linha em `explorador_eventos`, apontando para `zip_id` e `xml_entry_name`.
6. S-1210 e S-5002 recebem enriquecimento em `dados_json` para alimentar analises, S-1210 anual e validacoes.
7. O chain walk cria `timeline_mes`, `timeline_envio` e `timeline_envio_item` por `per_apur`.
8. XML original permanece no ZIP bruto; XML enviado/alterado e XML de retorno ficam em `timeline_envio_item.xml_enviado_oid` e `xml_retorno_oid` quando houver envio.

## Roteiro quando o certificado e os ZIPs forem entregues

1. Confirmar CNPJ, razao social oficial, slug/schema desejado e usuarios que devem enxergar a empresa.
2. Validar o certificado A1 localmente sem imprimir a senha.
3. Criar schema novo no Dados DB e aplicar migrations `empresa_v1.0.0` e `empresa_v1.1.0`.
4. Cadastrar `sistema.empresas_routing` e vinculos em `sistema.user_empresas`.
5. Seedar `master_empresas`, `config_esocial` e tabelas auxiliares necessarias no schema novo.
6. Inserir ou subir o certificado A1 no schema da empresa com a senha criptografada.
7. Escanear os 12 ZIPs antes de importar, conferindo `per_apur`, tipos de evento e quantidade de XMLs.
8. Importar os ZIPs para `empresa_zips_brutos` e extrair os XMLs para `explorador_eventos`.
9. Rodar e validar o backfill de timeline/chain walk para os 12 meses.
10. Auditar contagens por mes e tipo: S-1210, S-5002, S-1200, S-2200, S-2299, S-3000 e demais eventos presentes.
11. Verificar recuperacao dos XMLs originais e renderizacao do S-1210 anual no frontend.
12. Somente enviar ou consultar eSocial depois de autorizacao explicita do usuario.

## Pontos de atencao antes da terceira empresa

- O auth e o seletor de empresas ja funcionam por CNPJ via `X-Empresa-CNPJ`.
- Algumas rotas/telas antigas ainda dependem de `empresa_id` numerico.
- Hoje o mapeamento legado conhecido e APPA=1 e SOLUCOES=2.
- Para uma terceira empresa, e preciso escolher uma destas estrategias:
  - caminho rapido: registrar um novo `empresa_id` legado, ajustar `tenant.py` e o store `empresa.ts` para mapear CNPJ -> id;
  - caminho correto: migrar Explorer, S-1210 anual, certificado e envio para usarem CNPJ/header diretamente.
- A rota atual de certificado ainda precisa ser tratada com cuidado porque ha trecho single-tenant/TODO multi-tenant.
- Importar ZIPs fornecidos pelo usuario nao consome cota de Download do eSocial. Download/ConsultarIdentificadores/SolicitarDownload continuam proibidos sem autorizacao explicita.

## Entradas que o usuario deve fornecer

- Caminho do arquivo `.pfx` ou `.p12` do certificado.
- Caminho do arquivo com a senha do certificado, ou senha digitada diretamente pelo usuario quando necessario.
- Caminho da pasta com os 12 ZIPs mensais.
- CNPJ e razao social da nova empresa.
- Quais usuarios devem ter acesso e com qual papel.
