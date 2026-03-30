# =============================================================================
# Easy Social — Script de Exportação de Dados para Supabase
# =============================================================================
# USO: .\supabase\export_data.ps1
# PRÉ-REQUISITOS: PostgreSQL 16 instalado, bancos locais rodando
# =============================================================================

param(
    [string]$OutputDir = ".\supabase\data_dumps",
    [string]$PgDump = "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
    [string]$DbHost = "localhost",
    [string]$DbUser = "easy_social_user",
    [string]$DbPassword = "sua_senha_segura"
)

$env:PGPASSWORD = $DbPassword

# Criar diretório de saída
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "=== Exportando dados de easy_social_db ===" -ForegroundColor Cyan

& $PgDump -h $DbHost -U $DbUser -d easy_social_db `
    --data-only --inserts --no-owner --no-privileges `
    --exclude-table-data='analise_natureza_certo' `
    2>$null | Out-File -Encoding utf8 "$OutputDir\data_easy_social_db.sql"

Write-Host "  -> $OutputDir\data_easy_social_db.sql" -ForegroundColor Green

Write-Host "=== Exportando dados de easy_social_master ===" -ForegroundColor Cyan

& $PgDump -h $DbHost -U $DbUser -d easy_social_master `
    --data-only --inserts --no-owner --no-privileges `
    2>$null | Out-File -Encoding utf8 "$OutputDir\data_easy_social_master_raw.sql"

# Reescrever tabelas do master para schema "master."
$masterContent = Get-Content "$OutputDir\data_easy_social_master_raw.sql" -Raw
$masterContent = $masterContent -replace 'INSERT INTO public\.empresas', 'INSERT INTO master.empresas'
$masterContent = $masterContent -replace 'INSERT INTO public\.usuarios', '-- SKIP: usuarios migrados para Supabase Auth -- INSERT INTO public.usuarios'
$masterContent = $masterContent -replace 'INSERT INTO public\.usuario_empresa', 'INSERT INTO master.usuario_empresa'
$masterContent = $masterContent -replace 'INSERT INTO public\.naturezas_esocial', 'INSERT INTO master.naturezas_esocial'
$masterContent | Out-File -Encoding utf8 "$OutputDir\data_easy_social_master.sql"

Remove-Item "$OutputDir\data_easy_social_master_raw.sql" -Force

Write-Host "  -> $OutputDir\data_easy_social_master.sql" -ForegroundColor Green

# Contagem de linhas
$dbLines = (Get-Content "$OutputDir\data_easy_social_db.sql" | Measure-Object).Count
$masterLines = (Get-Content "$OutputDir\data_easy_social_master.sql" | Measure-Object).Count

Write-Host ""
Write-Host "=== Exportação completa ===" -ForegroundColor Green
Write-Host "  easy_social_db:     $dbLines linhas"
Write-Host "  easy_social_master: $masterLines linhas"
Write-Host ""
Write-Host "Próximo passo: importar no Supabase:" -ForegroundColor Yellow
Write-Host "  1. Rode a migration: supabase\migrations\20260330000000_initial_schema.sql"
Write-Host "  2. Importe dados DB: psql <SUPABASE_URL> < $OutputDir\data_easy_social_db.sql"
Write-Host "  3. Importe dados Master: psql <SUPABASE_URL> < $OutputDir\data_easy_social_master.sql"
Write-Host "  4. Recrie usuários via Supabase Auth (signup manual ou seed)"
