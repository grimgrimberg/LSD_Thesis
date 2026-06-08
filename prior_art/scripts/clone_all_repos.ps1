<#
.SYNOPSIS
    Clone or inspect public prior-art GitHub repositories.

.DESCRIPTION
    Reads prior_art/repository_sources.json, clones each listed public GitHub
    repository into prior_art/repositories/, and writes repository metadata to
    prior_art/repository_manifest.json and prior_art/repository_manifest.md.

    The script does not write files inside cloned repositories. This keeps
    upstream code unmodified while still recording the checked commit hashes.

.PARAMETER DryRun
    Print planned clone targets without network or filesystem changes.

.PARAMETER UpdateExisting
    Fetch existing repositories before recording metadata. Disabled by default
    so already-cloned evidence does not drift silently.

.EXAMPLE
    .\prior_art\scripts\clone_all_repos.ps1

.EXAMPLE
    .\prior_art\scripts\clone_all_repos.ps1 -DryRun
#>

param(
    [switch]$DryRun,
    [switch]$UpdateExisting
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$priorArtRoot = Split-Path -Parent $scriptDir
$repoRoot = Join-Path $priorArtRoot "repositories"
$sourcePath = Join-Path $priorArtRoot "repository_sources.json"
$manifestJsonPath = Join-Path $priorArtRoot "repository_manifest.json"
$manifestMdPath = Join-Path $priorArtRoot "repository_manifest.md"

if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "Repository source list not found: $sourcePath"
}

$source = Get-Content -Raw -LiteralPath $sourcePath | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $repoRoot)) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would create directory: $repoRoot"
    } else {
        New-Item -ItemType Directory -Path $repoRoot -Force | Out-Null
        Write-Host "[INFO] Created directory: $repoRoot"
    }
}

function Get-FirstFileName {
    param(
        [Parameter(Mandatory=$true)][string]$Directory,
        [Parameter(Mandatory=$true)][string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        $match = Get-ChildItem -LiteralPath $Directory -File -Filter $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) {
            return $match.Name
        }
    }
    return $null
}

function Get-GitValue {
    param(
        [Parameter(Mandatory=$true)][string]$Directory,
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )

    $output = & git -C $Directory @Arguments 2>$null
    if ($LASTEXITCODE -eq 0) {
        return ($output | Select-Object -First 1)
    }
    return $null
}

function Invoke-GitLogged {
    param(
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & git @Arguments 2>&1 | ForEach-Object { Write-Host "    $_" }
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

$manifestEntries = @()

Write-Host ""
Write-Host "============================================================"
Write-Host "  Prior-Art Repository Cloner"
Write-Host "  Target: $repoRoot"
Write-Host "  Sources: $($source.repositories.Count)"
Write-Host "============================================================"
Write-Host ""

foreach ($repo in $source.repositories) {
    $destPath = Join-Path $repoRoot $repo.directory
    $status = "planned"
    $errorMessage = $null

    Write-Host "--- $($repo.directory) ---"

    if ($DryRun) {
        Write-Host "  [DRY-RUN] Would clone or inspect $($repo.url)"
    } else {
        try {
            if (Test-Path -LiteralPath $destPath) {
                if (Test-Path -LiteralPath (Join-Path $destPath ".git")) {
                    if ($UpdateExisting) {
                        Write-Host "  [INFO] Existing repo found; fetching updates."
                        $exitCode = Invoke-GitLogged -Arguments @("-C", $destPath, "fetch", "--prune")
                        if ($exitCode -ne 0) {
                            throw "git fetch exited with code $exitCode"
                        }
                        $status = "existing-fetched"
                    } else {
                        Write-Host "  [INFO] Existing repo found; not updating."
                        $status = "existing"
                    }
                } else {
                    $status = "blocked"
                    $errorMessage = "Destination exists but is not a Git repository."
                    Write-Host "  [WARN] $errorMessage"
                }
            } else {
                Write-Host "  [INFO] Cloning $($repo.url)"
                $exitCode = Invoke-GitLogged -Arguments @("clone", "--depth", "1", $repo.url, $destPath)
                if ($exitCode -ne 0) {
                    throw "git clone exited with code $exitCode"
                }
                $status = "cloned"
            }
        } catch {
            $status = "error"
            $errorMessage = $_.Exception.Message
            Write-Host "  [ERROR] $errorMessage"
        }
    }

    $isGit = $false
    $head = $null
    $branch = $null
    $remote = $null
    $readme = $null
    $license = $null

    if ((Test-Path -LiteralPath $destPath) -and (Test-Path -LiteralPath (Join-Path $destPath ".git"))) {
        $isGit = $true
        $head = Get-GitValue -Directory $destPath -Arguments @("rev-parse", "HEAD")
        $branch = Get-GitValue -Directory $destPath -Arguments @("branch", "--show-current")
        $remote = Get-GitValue -Directory $destPath -Arguments @("remote", "get-url", "origin")
        $readme = Get-FirstFileName -Directory $destPath -Patterns @("README*", "readme*")
        $license = Get-FirstFileName -Directory $destPath -Patterns @("LICENSE*", "LICENCE*", "COPYING*")
    }

    $manifestEntries += [PSCustomObject]@{
        family = $repo.family
        name = $repo.name
        url = $repo.url
        directory = $repo.directory
        role = $repo.role
        expected_language = $repo.expected_language
        expected_ds003059_support = $repo.expected_ds003059_support
        status = $status
        error = $errorMessage
        local_path = $destPath
        is_git_repository = $isGit
        checked_commit = $head
        checked_branch = $branch
        remote_url = $remote
        readme_file = $readme
        license_file = $license
        checked_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    }

    if ($head) {
        Write-Host "  [OK] Commit: $($head.Substring(0, [Math]::Min(12, $head.Length)))"
    }
    Write-Host ""
}

if (-not $DryRun) {
    $manifest = [PSCustomObject]@{
        schema = "prior_art.repository_manifest.v1"
        generated_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
        repository_root = $repoRoot
        entries = $manifestEntries
        non_clone_sources = $source.non_clone_sources
    }

    $manifest | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $manifestJsonPath -Encoding utf8

    $md = New-Object System.Collections.Generic.List[string]
    $md.Add("# Repository Manifest")
    $md.Add("")
    $md.Add("Generated by `prior_art/scripts/clone_all_repos.ps1`.")
    $md.Add("")
    $md.Add("Cloned repositories are kept in `prior_art/repositories/` and are gitignored. This manifest records the checked commits without modifying upstream code.")
    $md.Add("")
    $md.Add("| Family | Repository | Status | Branch | Commit | README | License | Role |")
    $md.Add("|---|---|---:|---|---|---|---|---|")
    foreach ($entry in $manifestEntries) {
        $commit = if ($entry.checked_commit) { $entry.checked_commit.Substring(0, [Math]::Min(12, $entry.checked_commit.Length)) } else { "-" }
        $branchText = if ($entry.checked_branch) { $entry.checked_branch } else { "-" }
        $readmeText = if ($entry.readme_file) { $entry.readme_file } else { "-" }
        $licenseText = if ($entry.license_file) { $entry.license_file } else { "-" }
        $md.Add("| $($entry.family) | [$($entry.name)]($($entry.url)) | $($entry.status) | $branchText | $commit | $readmeText | $licenseText | $($entry.role) |")
    }
    $md.Add("")
    $md.Add("## Non-Clone Sources")
    $md.Add("")
    $md.Add("| Family | Source | Role | Policy |")
    $md.Add("|---|---|---|---|")
    foreach ($sourceEntry in $source.non_clone_sources) {
        $md.Add("| $($sourceEntry.family) | [$($sourceEntry.name)]($($sourceEntry.url)) | $($sourceEntry.role) | $($sourceEntry.clone_policy) |")
    }

    $md | Out-File -LiteralPath $manifestMdPath -Encoding utf8
    Write-Host "[INFO] Wrote manifest: $manifestJsonPath"
    Write-Host "[INFO] Wrote manifest: $manifestMdPath"
}

Write-Host ""
Write-Host "Done."
