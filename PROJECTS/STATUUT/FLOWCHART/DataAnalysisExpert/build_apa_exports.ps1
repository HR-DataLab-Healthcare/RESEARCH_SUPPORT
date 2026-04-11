param(
    [string]$SourceMarkdown = "D:\OneDrive - Hogeschool Rotterdam\1_CURRENT_DOCUMENTS\DATALAB_ALIGNMENT\DATALAB_STATUUT\DATALAB_STATUUT_GENERIC_FORMAT_2026_V01.md",
    [string]$OutputDirectory = "D:\OneDrive - Hogeschool Rotterdam\1_CURRENT_DOCUMENTS\DATALAB_ALIGNMENT\DATALAB_STATUUT\DataAnalysisExpert"
)

$ErrorActionPreference = 'Stop'

function Convert-HostToOrg {
    param([string]$HostName)

    if (-not $HostName) {
        return ''
    }

    $cleanHost = $HostName.Trim().ToLowerInvariant()
    $cleanHost = $cleanHost -replace '^https?://', ''
    $cleanHost = $cleanHost -replace '/.*$', ''
    $cleanHost = $cleanHost -replace '^www\.', ''

    $parts = $cleanHost -split '\.'
    if ($parts.Count -ge 2) {
        if ($parts[-2] -eq 'co' -and $parts.Count -ge 3) {
            $root = $parts[-3]
        }
        else {
            $root = $parts[-2]
        }
    }
    else {
        $root = $cleanHost
    }

    $root = $root -replace '-', ' '
    $textInfo = (Get-Culture).TextInfo
    return $textInfo.ToTitleCase($root)
}

function Get-InferredYear {
    param(
        [string]$Title,
        [string]$Url
    )

    foreach ($value in @($Title, $Url)) {
        if ($value -match '(19|20)\d{2}') {
            return $matches[0]
        }
    }

    return 'z.d.'
}

function Get-ReferenceData {
    param(
        [int]$Number,
        [string]$Domain,
        [string]$Title,
        [string]$Url,
        [hashtable]$ManualOverrides
    )

    if ($ManualOverrides.ContainsKey($Number)) {
        $override = $ManualOverrides[$Number]
        $author = $override.Author
        $cleanTitle = $override.Title
        $year = if ($override.ContainsKey('Year')) { $override.Year } else { Get-InferredYear -Title $cleanTitle -Url $Url }
    }
    else {
        $cleanTitle = ($Title -replace '\\\|', '|' -replace '\s+', ' ').Trim(' ', '-', ':', '|')
        $author = ''

        if ($cleanTitle -match '\s-\s(?<site>[^-|][^-]+)$') {
            $author = $matches['site'].Trim()
        }
        elseif ($cleanTitle -match '\|\s*(?<site>[^|]+)$') {
            $author = $matches['site'].Trim()
        }

        if (-not $author) {
            if ($Domain) {
                $author = Convert-HostToOrg -HostName $Domain
            }
            elseif ($Url) {
                $author = Convert-HostToOrg -HostName ([uri]$Url).Host
            }
        }

        foreach ($suffix in @(" - $author", " | $author")) {
            if ($author -and $cleanTitle.EndsWith($suffix, [System.StringComparison]::OrdinalIgnoreCase)) {
                $cleanTitle = $cleanTitle.Substring(0, $cleanTitle.Length - $suffix.Length).Trim()
            }
        }

        $year = Get-InferredYear -Title $cleanTitle -Url $Url
    }

    if (-not $author) {
        $author = 'Bron onbekend'
    }

    $citationAuthor = $author
    $citationAuthor = $citationAuthor -replace '\s*\([^\)]*\)$', ''

    return [pscustomobject]@{
        Number = $Number
        Author = $author.Trim()
        Title = $cleanTitle.Trim()
        Year = $year
        Url = $Url.Trim()
        Citation = "$citationAuthor, $year"
        Anchor = "ref-$Number"
    }
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$baseName = [System.IO.Path]::GetFileNameWithoutExtension($SourceMarkdown)
$outputMarkdown = Join-Path $OutputDirectory ($baseName + '_APA.md')
$outputDocx = Join-Path $OutputDirectory ($baseName + '_APA.docx')
$outputHtml = Join-Path $OutputDirectory ($baseName + '_APA.html')
$pandoc = 'C:\Users\PROMET02\anaconda3\Library\bin\pandoc.exe'

$sourceText = Get-Content -LiteralPath $SourceMarkdown -Raw
$usedCitationNumbers = [regex]::Matches($sourceText, '<sup>(\d+)</sup>') |
    ForEach-Object { [int]$_.Groups[1].Value } |
    Sort-Object -Unique

$rawEntries = New-Object System.Collections.Generic.List[object]
foreach ($line in (Get-Content -LiteralPath $SourceMarkdown)) {
    if ($line -match '^\d+\.\s+\[(?<label>.+?)\]\((?<url>https?://[^\)]+)\)\s*$') {
        $label = $matches['label']
        $url = $matches['url'].Trim()
        $label = $label -replace '<img[^>]*>', ''
        $label = $label -replace 'Opens in a new window', ''
        $label = ($label -replace '\s+', ' ').Trim()

        $domain = ''
        $title = $label
        if ($label -match '^(?<domain>[A-Za-z0-9.-]+?\.(?:nl|be|org|com|edu|gov|ca|eu|io))(?<title>.*)$') {
            $domain = $matches['domain']
            $title = $matches['title'].Trim()
        }

        $rawEntries.Add([pscustomobject]@{
            Domain = $domain
            Title = $title
            Url = $url
        })
    }
}

$manualOverrides = @{
    5 = @{ Author = 'Katholiek Onderwijs Vlaanderen'; Title = 'Model intern reglement vzw-leersteuncentrumbestuur'; Year = '2023' }
    15 = @{ Author = 'Federale overheidsdienst Justitie'; Title = 'Statuten'; Year = 'z.d.' }
    27 = @{ Author = 'MST'; Title = 'Privacyrichtlijnen voor wetenschappelijk onderzoek met patientgegevens in de STZ-huizen'; Year = '2020' }
    39 = @{ Author = 'Data voor gezondheid'; Title = 'ECP | Handleiding - Aanpak begeleidingsethiek voor AI in de zorg'; Year = '2021' }
    41 = @{ Author = 'DAMA NL'; Title = 'Data Science Governance Framework'; Year = '2023' }
    43 = @{ Author = 'Data voor gezondheid'; Title = 'TNO2024 R10662 Generatieve AI in de Nederlandse zorg'; Year = '2024' }
    48 = @{ Author = 'Autoriteit Persoonsgegevens'; Title = 'Autoriteit Persoonsgegevens'; Year = 'z.d.' }
    49 = @{ Author = 'Data voor gezondheid'; Title = 'Health Data Access Body (HDAB)'; Year = 'z.d.' }
    51 = @{ Author = 'Hogeschool Rotterdam'; Title = 'HR Datalab Healthcare'; Year = 'z.d.' }
    52 = @{ Author = 'ZonMw'; Title = 'Multidisciplinaire samenwerking in de eerste lijn'; Year = 'z.d.' }
    55 = @{ Author = 'Shakudo'; Title = 'Healthcare Data Stack: A Guide to Building a Modern Data Stack'; Year = 'z.d.' }
    57 = @{ Author = 'Movisie'; Title = 'Bijlage 1: Voorbeeld omgangsregels'; Year = '2019' }
    58 = @{ Author = 'Gezond en veilig werken'; Title = 'Voorbeeld gedragsregels ongewenst gedrag'; Year = '2024' }
    61 = @{ Author = 'Open Cultuur Data'; Title = 'Open Cultuur Data Lab sessie: Juridische kaders'; Year = '2016' }
    62 = @{ Author = 'SURF'; Title = 'De juridische status van ruwe data: een wegwijzer voor de onderzoekspraktijk'; Year = 'z.d.' }
    63 = @{ Author = 'ADaSci'; Title = 'Ethical & Standards for Chartered Data Scientists (CDS)'; Year = 'z.d.' }
    64 = @{ Author = 'The University of Arizona'; Title = 'Code of conduct'; Year = 'z.d.' }
    65 = @{ Author = 'Business Management Daily'; Title = 'The top 10 HR analytics tools to use in 2023'; Year = '2023' }
    66 = @{ Author = 'Bytesnet'; Title = 'Groningen'; Year = 'z.d.' }
    67 = @{ Author = 'Bytesnet'; Title = "Groningen - d'ROOT"; Year = 'z.d.' }
    69 = @{ Author = 'Teradata'; Title = 'Requests - Teradata Data Lab'; Year = '2018' }
    70 = @{ Author = 'Tilburg University'; Title = 'Data Lab'; Year = 'z.d.' }
    72 = @{ Author = 'Rijksuniversiteit Groningen'; Title = 'Essentiele aspecten van privacy en security in onderzoek'; Year = 'z.d.' }
    73 = @{ Author = 'De Haagse Hogeschool'; Title = 'Wetgeving'; Year = 'z.d.' }
    74 = @{ Author = 'Emerce'; Title = 'Onderzoek: Helft Nederlandse bedrijven is gevoelige data kwijtgeraakt in het afgelopen jaar'; Year = 'z.d.' }
    75 = @{ Author = 'ALLEA'; Title = 'Europese gedragscode voor wetenschappelijke integriteit'; Year = '2018' }
    76 = @{ Author = 'ALLEA'; Title = 'The European Code of Conduct for Research Integrity'; Year = '2023' }
    78 = @{ Author = 'Data Science Collective'; Title = 'The Three Layers of the Modern Data Stack: A Practical Guide for the Uninitiated'; Year = 'z.d.' }
}

$referenceMap = @{}
foreach ($number in $usedCitationNumbers) {
    if ($number -gt $rawEntries.Count) {
        continue
    }

    $entry = $rawEntries[$number - 1]
    $referenceMap[$number] = Get-ReferenceData -Number $number -Domain $entry.Domain -Title $entry.Title -Url $entry.Url -ManualOverrides $manualOverrides
}

$bodyText = [regex]::Replace($sourceText, '(?s)\r?\n## Bronnenlijst.*$', '')
$bodyText = [regex]::Replace($bodyText, '<sup>(\d+)</sup>', {
    param($match)

    $number = [int]$match.Groups[1].Value
    if ($referenceMap.ContainsKey($number)) {
        $citationText = $referenceMap[$number].Citation
        return " ([${citationText}](#ref-$number))"
    }

    return $match.Value
})
$bodyText = $bodyText.TrimEnd()

$sortedReferences = $referenceMap.Values | Sort-Object Author, Year, Title
$referenceLines = New-Object System.Collections.Generic.List[string]
$referenceLines.Add('## Bronnenlijst')
$referenceLines.Add('')
$referenceLines.Add('Onderstaande referenties zijn afgeleid uit de oorspronkelijke bronvermelding en geformatteerd in een APA-achtige webreferentiestijl.')
$referenceLines.Add('')
foreach ($reference in $sortedReferences) {
    $referenceLines.Add(("<a id=`"{0}`"></a>" -f $reference.Anchor))
    $referenceLines.Add('')
    $referenceLines.Add(("{0}. ({1}). *{2}.* <{3}>" -f $reference.Author, $reference.Year, $reference.Title, $reference.Url))
    $referenceLines.Add('')
}

$finalMarkdown = $bodyText + "`r`n`r`n" + ($referenceLines -join "`r`n") + "`r`n"
Set-Content -LiteralPath $outputMarkdown -Value $finalMarkdown -Encoding UTF8

& $pandoc $outputMarkdown -f 'gfm+raw_html+pipe_tables' -t docx --wrap=none --resource-path=$OutputDirectory -o $outputDocx
& $pandoc $outputMarkdown -f 'gfm+raw_html+pipe_tables' -t html5 --standalone --embed-resources --wrap=none --resource-path=$OutputDirectory -o $outputHtml

Write-Output "MARKDOWN=$outputMarkdown"
Write-Output "DOCX=$outputDocx"
Write-Output "HTML=$outputHtml"
