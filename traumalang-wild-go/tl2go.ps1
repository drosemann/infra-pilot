# Portiert traumalang-wild/out/*.tl 1:1 nach Go (out-go/*.go). Explizit per Hand starten.
param(
    [string]$InDir = (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') 'traumalang-wild') 'out'),
    [string]$OutDir = (Join-Path $PSScriptRoot 'out-go')
)
$ErrorActionPreference = 'Stop'
$files = Get-ChildItem -Path $InDir -Filter '*.tl'
if ($files.Count -eq 0) { throw "keine .tl-Dateien in $InDir" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
foreach ($f in $files) {
    $out = [System.Collections.Generic.List[string]]::new()
    foreach ($line in [System.IO.File]::ReadAllLines($f.FullName)) {
        if ($line -eq "IT'S SHOWTIME") {
            $out.Add('package main'); $out.Add(''); $out.Add('import "fmt"'); $out.Add(''); $out.Add('func main() {')
        } elseif ($line -eq 'YOU HAVE BEEN TERMINATED') {
            $out.Add('}')
        } elseif ($line.StartsWith('PUT IT IN JIRA ') -or $line.StartsWith('WE NEED TO TAKE THIS OFFLINE ') -or $line -eq 'THIS COULD HAVE BEEN AN EMAIL') {
            $out.Add("`t// $line")
        } elseif ($line.StartsWith('TALK TO THE HAND "') -and $line.EndsWith('"') -and $line.Length -gt 20) {
            $out.Add("`tfmt.Println(`"$($line.Substring(18, $line.Length - 19))`")")
        } else {
            $out.Add("`t// UNTRANSLATED: $line")
        }
    }
    [System.IO.File]::WriteAllLines((Join-Path $OutDir ($f.BaseName + '.go')), $out, (New-Object System.Text.UTF8Encoding $false))
}
Write-Host "portiert: $($files.Count) Dateien -> $OutDir"
