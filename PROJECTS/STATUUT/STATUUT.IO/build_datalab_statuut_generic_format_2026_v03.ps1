[CmdletBinding()]
param(
    [string]$SourceFile = "DATALAB_STATUUT_GENERIC_FORMAT_2026_V03.md",
    [string]$OutputFile = "DATALAB_STATUUT_GENERIC_FORMAT_2026_V03.html"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-MermaidRenderSvg {
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [Parameter(Mandatory = $true)][string]$OutputPath
    )

    Get-Command npx -ErrorAction Stop | Out-Null
    & npx -y @mermaid-js/mermaid-cli -i $InputPath -o $OutputPath -b white | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Mermaid rendering failed for $InputPath"
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePath = Join-Path $scriptRoot $SourceFile
$outputPath = Join-Path $scriptRoot $OutputFile
$templatePath = Join-Path $scriptRoot "template_datalab_statuut_generic_format_2026_v03.html5"
$figuresDir = Join-Path $scriptRoot "figures"
$buildDir = Join-Path $scriptRoot "_build"
$processedMarkdownPath = Join-Path $buildDir "DATALAB_STATUUT_GENERIC_FORMAT_2026_V03_processed.md"
$pandocPath = "C:\Users\PROMET02\anaconda3\Library\bin\pandoc.exe"

if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "Source file not found: $sourcePath"
}

if (-not (Test-Path -LiteralPath $templatePath)) {
    throw "Template file not found: $templatePath"
}

if (-not (Test-Path -LiteralPath $pandocPath)) {
    throw "Pandoc executable not found: $pandocPath"
}

if (Test-Path -LiteralPath $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}

New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
New-Item -ItemType Directory -Path $figuresDir -Force | Out-Null
Get-ChildItem -Path $figuresDir -Filter 'mermaid-*.svg' -File -ErrorAction SilentlyContinue | Remove-Item -Force

$content = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8

$navToc = '<ol class="toc"></ol>'
$sourceLines = Get-Content -LiteralPath $sourcePath -Encoding UTF8
$inToc = $false
$tocEntries = New-Object System.Collections.Generic.List[object]

foreach ($line in $sourceLines) {
    if (-not $inToc) {
        if ($line -match '^##\s+Inhoudsopgave\s*$') {
            $inToc = $true
        }
        continue
    }

    if ($line -match '^<a id=') {
        break
    }

    if ($line -match '^- \[(?<text>[^\]]+)\]\((?<href>#[^)]+)\)\s*$') {
        $tocEntries.Add([PSCustomObject]@{
            Text = $matches['text']
            Href = $matches['href']
        })
    }
}

if ($tocEntries.Count -gt 0) {
    $tocItems = for ($i = 0; $i -lt $tocEntries.Count; $i++) {
        '<li class="tocline"><a class="tocxref" href="' + $tocEntries[$i].Href + '"><span class="secno">' + ($i + 1) + '. </span>' + $tocEntries[$i].Text + '</a></li>'
    }
    $navToc = '<ol class="toc">' + ($tocItems -join '') + '</ol>'
}

$script:mermaidIndex = 0
$content = [regex]::Replace(
    $content,
    '```mermaid\s*\r?\n(?<body>[\s\S]*?)\r?\n```',
    {
        param($match)

        $script:mermaidIndex += 1
        $diagramName = "mermaid-{0:d2}" -f $script:mermaidIndex
        $diagramText = $match.Groups['body'].Value.Trim()
        $diagramText = [regex]::Replace($diagramText, '\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]', '[$1, $2]')

        $mmdPath = Join-Path $buildDir ($diagramName + '.mmd')
        $svgPath = Join-Path $figuresDir ($diagramName + '.svg')

        Set-Content -LiteralPath $mmdPath -Value $diagramText -Encoding UTF8
        Invoke-MermaidRenderSvg -InputPath $mmdPath -OutputPath $svgPath

        return [Environment]::NewLine + '<figure class="diagram overlarge"><img src="figures/' + $diagramName + '.svg" alt="Diagram ' + $script:mermaidIndex + '" /></figure>' + [Environment]::NewLine
    },
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)

Set-Content -LiteralPath $processedMarkdownPath -Value $content -Encoding UTF8

& $pandocPath $processedMarkdownPath `
    -f markdown+gfm_auto_identifiers+raw_html+pipe_tables+bracketed_spans `
    -t html5 `
    --standalone `
    --section-divs `
    --template=$templatePath `
    --metadata=lang:nl `
    --metadata=pagetitle:"Statuut van het HR Healthcare DataLab" `
    -o $outputPath

if ($LASTEXITCODE -ne 0) {
    throw "Pandoc HTML conversion failed."
}

$html = Get-Content -LiteralPath $outputPath -Raw -Encoding UTF8
$html = $html.Replace('<ol class="toc"></ol>', $navToc)
Set-Content -LiteralPath $outputPath -Value $html -Encoding UTF8

Write-Host "Created $outputPath"
