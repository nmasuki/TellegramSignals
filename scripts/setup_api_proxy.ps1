#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Sets up local DNS and port proxy so http://api.blackcandle.co routes to
    the TelegramSignals API at http://localhost:4726.

.DESCRIPTION
    1. Adds a hosts file entry:  127.0.0.1  api.blackcandle.co
    2. Creates a netsh portproxy rule:  127.0.0.1:80 -> 127.0.0.1:4726
    3. Adds a firewall rule to allow inbound TCP on port 80 (loopback).

    Run with:  powershell -ExecutionPolicy Bypass -File setup_api_proxy.ps1
    To undo:   powershell -ExecutionPolicy Bypass -File setup_api_proxy.ps1 -Remove

.PARAMETER Remove
    Removes the hosts entry, port proxy rule, and firewall rule.
#>

param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

$hostname   = "api.blackcandle.co"
$listenPort = 80
$targetPort = 4726
$listenAddr = "127.0.0.1"
$targetAddr = "127.0.0.1"
$hostsPath  = "$env:SystemRoot\System32\drivers\etc\hosts"
$fwRuleName = "TelegramSignals API (port 80 loopback)"
$hostsEntry = "$listenAddr $hostname"

function Write-Step($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Skip($msg)  { Write-Host "[-] $msg" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# REMOVE mode
# ---------------------------------------------------------------------------
if ($Remove) {
    Write-Host "`nRemoving api.blackcandle.co proxy setup...`n" -ForegroundColor Red

    # 1. Hosts file
    Write-Step "Removing hosts entry"
    $content = Get-Content $hostsPath -Raw
    if ($content -match [regex]::Escape($hostsEntry)) {
        $content = ($content -split "`r?`n" | Where-Object { $_ -notmatch [regex]::Escape($hostsEntry) -and $_ -notmatch "# TelegramSignals API" }) -join "`r`n"
        Set-Content -Path $hostsPath -Value $content -Encoding ASCII -NoNewline
        Write-OK "Hosts entry removed"
    } else {
        Write-Skip "Hosts entry not found, skipping"
    }

    # 2. Port proxy
    Write-Step "Removing port proxy rule"
    netsh interface portproxy delete v4tov4 listenport=$listenPort listenaddress=$listenAddr 2>$null
    Write-OK "Port proxy rule removed"

    # 3. Firewall
    Write-Step "Removing firewall rule"
    Remove-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
    Write-OK "Firewall rule removed"

    Write-Host "`nDone. Proxy setup has been removed.`n" -ForegroundColor Green
    exit 0
}

# ---------------------------------------------------------------------------
# INSTALL mode
# ---------------------------------------------------------------------------
Write-Host "`nSetting up http://api.blackcandle.co -> http://localhost:$targetPort`n" -ForegroundColor Cyan

# 1. Hosts file entry
Write-Step "Adding hosts file entry: $hostsEntry"
$hostsContent = Get-Content $hostsPath -Raw
if ($hostsContent -match [regex]::Escape($hostsEntry)) {
    Write-Skip "Hosts entry already exists, skipping"
} else {
    Add-Content -Path $hostsPath -Value "`r`n# TelegramSignals API`r`n$hostsEntry" -Encoding ASCII
    Write-OK "Hosts entry added"
}

# 2. Port proxy rule (netsh)
Write-Step "Adding port proxy: ${listenAddr}:${listenPort} -> ${targetAddr}:${targetPort}"
$existing = netsh interface portproxy show v4tov4 | Select-String "$listenAddr\s+$listenPort"
if ($existing) {
    Write-Skip "Port proxy rule already exists, updating"
}
netsh interface portproxy add v4tov4 `
    listenport=$listenPort `
    listenaddress=$listenAddr `
    connectport=$targetPort `
    connectaddress=$targetAddr
Write-OK "Port proxy rule set"

# 3. Firewall rule
Write-Step "Adding firewall rule for inbound TCP port $listenPort"
$fwExists = Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
if ($fwExists) {
    Write-Skip "Firewall rule already exists, skipping"
} else {
    New-NetFirewallRule `
        -DisplayName $fwRuleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $listenPort `
        -Action Allow `
        -Profile Any | Out-Null
    Write-OK "Firewall rule added"
}

# 4. Verify
Write-Host "`n--- Verification ---" -ForegroundColor Cyan
Write-Step "Hosts file:"
Select-String -Path $hostsPath -Pattern $hostname | ForEach-Object { Write-Host "    $_" }

Write-Step "Port proxy rules:"
netsh interface portproxy show v4tov4 | ForEach-Object { Write-Host "    $_" }

Write-Step "Firewall rule:"
Get-NetFirewallRule -DisplayName $fwRuleName | Format-Table DisplayName, Enabled, Direction, Action -AutoSize | Out-String | ForEach-Object { Write-Host "    $_" }

Write-Host "`nSetup complete! Make sure the API is running on port $targetPort, then visit:" -ForegroundColor Green
Write-Host "    http://api.blackcandle.co`n" -ForegroundColor White
