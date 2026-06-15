$out = 'C:\Users\xandao\AppData\Local\Temp\docx_pdf'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$wdFormatPDF = 17
foreach ($f in @('APPA_RELATORIO_2026 F.docx','SOLUCOES_RELATORIO_2026 F.docx','OBJETIVA_RELATORIO_2026 F.docx')) {
    $src = Join-Path $env:USERPROFILE "Downloads\$f"
    $dst = Join-Path $out (($f -replace ' F\.docx$','_F.pdf'))
    Write-Host "Opening: $src"
    $doc = $word.Documents.Open($src, $false, $true)
    $doc.SaveAs([ref]$dst, [ref]$wdFormatPDF)
    $doc.Close($false)
    Write-Host "Saved: $dst"
}
$word.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
Write-Host "DONE"
Get-ChildItem $out
