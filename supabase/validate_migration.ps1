# =============================================================================
# Easy Social — Validação Pós-Migração Supabase
# =============================================================================
# Compara dados no Supabase contra gabarito do banco local
# USO: .\supabase\validate_migration.ps1
# =============================================================================

param(
    [string]$SupaHost = "aws-1-us-east-2.pooler.supabase.com",
    [string]$SupaPort = "5432",
    [string]$SupaUser = "postgres.zpizibafccwsjgvplcum",
    [string]$SupaDb   = "postgres",
    [string]$SupaPass = "6.18.13.1.8Supa",
    [string]$PsqlPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
)

$env:PGPASSWORD = $SupaPass
$psql = $PsqlPath
$errors = 0
$passed = 0

function Run-Query($query) {
    & $psql -h $SupaHost -p $SupaPort -U $SupaUser -d $SupaDb -P pager=off --no-align --tuples-only -c $query 2>$null
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " VALIDACAO POS-MIGRACAO SUPABASE" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# =============================================
# TESTE 1: Contagem de linhas por tabela
# =============================================
Write-Host "--- TESTE 1: Contagem de linhas ---" -ForegroundColor Yellow

$expected_counts = @{
    "analise_natureza" = 455
    "analise_natureza_certo" = 455
    "auditoria_naturezas" = 91
    "base_ficha_financeira" = 0
    "config_esocial" = 1
    "correcoes_staging" = 91
    "cruzamento_eb" = 448
    "cruzamento_resultado" = 455
    "cruzamento_tabela_a" = 455
    "cruzamento_tabela_b" = 1145
    "cruzamento_uploads" = 1
    "dinamica" = 276
    "eb_skills_base_legal" = 534
    "esocial_depara" = 2381
    "esocial_envios" = 18
    "esocial_tabela3_natureza" = 203
    "naturezas_esocial" = 206
    "planilha_1" = 0
    "rubrica_corrections" = 385
    "senha_certificado_salva" = 0
    "tabela3_esocial_oficial" = 215
    "tabela_cruzamento" = 455
    "tabela_eb" = 1224
    "tabela_eventos_gl" = 1145
    "uploads" = 2
}

# NOTA: certificados_a1 NAO migra para Supabase (dado local)

foreach ($table in ($expected_counts.Keys | Sort-Object)) {
    $count = Run-Query "SELECT count(*) FROM public.$table;"
    $exp = $expected_counts[$table]
    if ($count -eq $exp) {
        Write-Host "  OK  $table = $count" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  FAIL  $table: esperado=$exp, obtido=$count" -ForegroundColor Red
        $errors++
    }
}

# Master tables (prefixadas com master_)
$master_counts = @{
    "master_empresas" = 1
    "master_naturezas_esocial" = 203
    "master_usuario_empresa" = 3
    "master_perfis" = 3
}

foreach ($table in ($master_counts.Keys | Sort-Object)) {
    $count = Run-Query "SELECT count(*) FROM public.$table;"
    $exp = $master_counts[$table]
    if ($count -eq $exp) {
        Write-Host "  OK  $table = $count" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  FAIL  $table: esperado=$exp, obtido=$count" -ForegroundColor Red
        $errors++
    }
}

Write-Host ""

# =============================================
# TESTE 2: Checksums MD5 (integridade dos dados)
# =============================================
Write-Host "--- TESTE 2: Checksums MD5 ---" -ForegroundColor Yellow

$expected_checksums = @{
    "cruzamento_eb" = "94f844bc1e023106776f8e9fd3884360"
    "esocial_envios" = "e81d4dbc36757dcb2bde3dbff045cecb"
    "esocial_depara" = "ac2cb566ce861ff0d032acbb26e89994"
    "naturezas_esocial" = "14c2726baf1c46e87ec24bb8449e91e0"
    "esocial_tabela3_natureza" = "6dbe830a10f2b0ca8f6da15344f8b276"
    "eb_skills_base_legal" = "62808dbe777b041f1e7641a97e439364"
    "rubrica_corrections" = "f569695b6f6896491c63b206717d7d36"
    "tabela_eventos_gl" = "27c1f47695cd804a09aa795a2eed323a"
    "tabela_eb" = "093012480c0153b3da61ee0a18bcbb46"
    "analise_natureza" = "1b105599d7ad5e891ba45753a43c8a69"
    "dinamica" = "f78df226934deab64150720e0893b4fb"
    "uploads" = "05448202eb15e2f011ed5796222d4f2f"
    "config_esocial" = "a12fca678d13adcadb1ba49f750efb97"
    "auditoria_naturezas" = "de60062036cd038bf3abb03fe3c6d068"
    "correcoes_staging" = "8af278a91b6c9d79ed1db0fb20054614"
}

$checksum_queries = @{
    "cruzamento_eb" = "SELECT md5(string_agg(cod_rubrica || ':' || COALESCE(incid_inss,'') || ':' || COALESCE(incid_irrf,'') || ':' || COALESCE(incid_fgts,''), '|' ORDER BY id)) FROM cruzamento_eb;"
    "esocial_envios" = "SELECT md5(string_agg(COALESCE(tipo_evento,'') || ':' || COALESCE(protocolo_envio,'') || ':' || COALESCE(status,''), '|' ORDER BY id)) FROM esocial_envios;"
    "esocial_depara" = "SELECT md5(string_agg(cod_rubrica || ':' || campo || ':' || valor_novo, '|' ORDER BY id)) FROM esocial_depara;"
    "naturezas_esocial" = "SELECT md5(string_agg(codigo || ':' || nome, '|' ORDER BY id)) FROM naturezas_esocial;"
    "esocial_tabela3_natureza" = "SELECT md5(string_agg(codigo::text || ':' || nome, '|' ORDER BY codigo)) FROM esocial_tabela3_natureza;"
    "eb_skills_base_legal" = "SELECT md5(string_agg(COALESCE(col_a,'') || ':' || COALESCE(col_b,''), '|' ORDER BY id)) FROM eb_skills_base_legal;"
    "rubrica_corrections" = "SELECT md5(string_agg(cod_rubrica || ':' || COALESCE(status,''), '|' ORDER BY id)) FROM rubrica_corrections;"
    "tabela_eventos_gl" = "SELECT md5(string_agg(COALESCE(col_a,'') || ':' || COALESCE(col_b,''), '|' ORDER BY id)) FROM tabela_eventos_gl;"
    "tabela_eb" = "SELECT md5(string_agg(COALESCE(col_a,'') || ':' || COALESCE(col_b,''), '|' ORDER BY id)) FROM tabela_eb;"
    "analise_natureza" = "SELECT md5(string_agg(COALESCE(col_a,'') || ':' || COALESCE(col_b,''), '|' ORDER BY id)) FROM analise_natureza;"
    "dinamica" = "SELECT md5(string_agg(COALESCE(col_a,'') || ':' || COALESCE(col_b,''), '|' ORDER BY id)) FROM dinamica;"
    "uploads" = "SELECT md5(string_agg(file_name || ':' || file_size::text, '|' ORDER BY id)) FROM uploads;"
    "config_esocial" = "SELECT md5(string_agg(cnpj || ':' || COALESCE(ini_valid_padrao,''), '|' ORDER BY id)) FROM config_esocial;"
    "auditoria_naturezas" = "SELECT md5(string_agg(COALESCE(codigoevento,'') || ':' || COALESCE(natureza_nova,''), '|' ORDER BY id)) FROM auditoria_naturezas;"
    "correcoes_staging" = "SELECT md5(string_agg(codigoevento || ':' || COALESCE(status,''), '|' ORDER BY id)) FROM correcoes_staging;"
}

foreach ($table in ($expected_checksums.Keys | Sort-Object)) {
    $result = Run-Query $checksum_queries[$table]
    $exp = $expected_checksums[$table]
    if ($result -eq $exp) {
        Write-Host "  OK  $table checksum match" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  FAIL  $table: esperado=$exp, obtido=$result" -ForegroundColor Red
        $errors++
    }
}

Write-Host ""

# =============================================
# TESTE 3: Registros sentinela (primeiro e último)
# =============================================
Write-Host "--- TESTE 3: Registros sentinela ---" -ForegroundColor Yellow

# Primeiro registro cruzamento_eb
$first_ce = Run-Query "SELECT cod_rubrica || '|' || COALESCE(incid_inss,'') || '|' || COALESCE(incid_irrf,'') || '|' || COALESCE(incid_fgts,'') FROM cruzamento_eb ORDER BY id LIMIT 1;"
if ($first_ce -eq "1|11|11|11") {
    Write-Host "  OK  cruzamento_eb primeiro registro" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  FAIL  cruzamento_eb primeiro: esperado='1|11|11|11', obtido='$first_ce'" -ForegroundColor Red
    $errors++
}

# Último registro cruzamento_eb
$last_ce = Run-Query "SELECT cod_rubrica || '|' || COALESCE(incid_inss,'') || '|' || COALESCE(incid_irrf,'') || '|' || COALESCE(incid_fgts,'') FROM cruzamento_eb ORDER BY id DESC LIMIT 1;"
if ($last_ce -eq "9281|0|9|0") {
    Write-Host "  OK  cruzamento_eb ultimo registro" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  FAIL  cruzamento_eb ultimo: esperado='9281|0|9|0', obtido='$last_ce'" -ForegroundColor Red
    $errors++
}

# Primeiro envio
$first_env = Run-Query "SELECT tipo_evento || '|' || modo || '|' || status || '|' || ambiente FROM esocial_envios ORDER BY id LIMIT 1;"
if ($first_env -eq "S-1010|alteracao|processado|2") {
    Write-Host "  OK  esocial_envios primeiro registro" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  FAIL  esocial_envios primeiro: esperado='S-1010|alteracao|processado|2', obtido='$first_env'" -ForegroundColor Red
    $errors++
}

# Empresa
$empresa = Run-Query "SELECT nome || '|' || cnpj FROM master_empresas ORDER BY id LIMIT 1;"
if ($empresa -eq "APPA SERVICOS TEMPORARIOS E EFETIVOS LTDA|05.969.071/0001-10") {
    Write-Host "  OK  master_empresas registro" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  FAIL  master_empresas: obtido='$empresa'" -ForegroundColor Red
    $errors++
}

Write-Host ""

# =============================================
# TESTE 4: Sequences (max id correto)
# =============================================
Write-Host "--- TESTE 4: Max IDs / Sequences ---" -ForegroundColor Yellow

$expected_max_ids = @{
    "cruzamento_eb" = 448
    "esocial_envios" = 18
    "uploads" = 2
    "analise_natureza" = 910
    "tabela_eb" = 1224
    "tabela_eventos_gl" = 1145
    "rubrica_corrections" = 1418
}

foreach ($table in ($expected_max_ids.Keys | Sort-Object)) {
    $max_id = Run-Query "SELECT max(id) FROM $table;"
    $exp = $expected_max_ids[$table]
    if ([int]$max_id -eq $exp) {
        Write-Host "  OK  $table max_id = $max_id" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  FAIL  $table max_id: esperado=$exp, obtido=$max_id" -ForegroundColor Red
        $errors++
    }
}

Write-Host ""

# =============================================
# TESTE 5: Certificados A1 NAO existe no Supabase
# =============================================
Write-Host "--- TESTE 5: certificados_a1 NAO migrado ---" -ForegroundColor Yellow
$cert_exists = Run-Query "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='certificados_a1';"
if ($cert_exists -eq "0") {
    Write-Host "  OK  certificados_a1 NAO existe no Supabase (correto!)" -ForegroundColor Green
    $passed++
} else {
    $cert_count = Run-Query "SELECT count(*) FROM certificados_a1;"
    Write-Host "  WARN  certificados_a1 EXISTE no Supabase com $cert_count registros (dados sensiveis!)" -ForegroundColor Yellow
    # Não conta como erro, mas avisa
}

Write-Host ""

# =============================================
# RESUMO
# =============================================
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " RESULTADO: $passed PASSED, $errors FAILED" -ForegroundColor $(if ($errors -eq 0) { "Green" } else { "Red" })
Write-Host "=============================================" -ForegroundColor Cyan

if ($errors -gt 0) {
    Write-Host "MIGRACAO TEM PROBLEMAS! Verifique os FAILs acima." -ForegroundColor Red
    exit 1
} else {
    Write-Host "MIGRACAO VALIDADA COM SUCESSO!" -ForegroundColor Green
    exit 0
}
