$ErrorActionPreference = "Stop"

$envFile = Join-Path $PSScriptRoot "..\mysite\mysite\.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }
    $parts = $line.Split("=", 2)
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    [System.Environment]::SetEnvironmentVariable($key, $value)
  }
}

function Get-FirstEnvValue([string[]]$names) {
  foreach ($name in $names) {
    $value = [System.Environment]::GetEnvironmentVariable($name)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value
    }
  }
  return $null
}

$mysqlUrl = Get-FirstEnvValue @("MYSQL_URL")
$mysqlHost = Get-FirstEnvValue @("MYSQLHOST", "MYSQL_HOST")
$mysqlPort = Get-FirstEnvValue @("MYSQLPORT", "MYSQL_PORT")
$mysqlDb = Get-FirstEnvValue @("MYSQLDATABASE", "MYSQL_DATABASE")
$mysqlUser = Get-FirstEnvValue @("MYSQLUSER", "MYSQL_USER")
$password = Get-FirstEnvValue @("MYSQLPASSWORD", "MYSQL_ROOT_PASSWORD")

# Normalize env vars so Django always sees a consistent set.
if ($mysqlHost) { [System.Environment]::SetEnvironmentVariable("MYSQLHOST", $mysqlHost) }
if ($mysqlPort) { [System.Environment]::SetEnvironmentVariable("MYSQLPORT", $mysqlPort) }
if ($mysqlDb) { [System.Environment]::SetEnvironmentVariable("MYSQLDATABASE", $mysqlDb) }
if ($mysqlUser) { [System.Environment]::SetEnvironmentVariable("MYSQLUSER", $mysqlUser) }
if ($password) { [System.Environment]::SetEnvironmentVariable("MYSQLPASSWORD", $password) }

$missing = @()
if ([string]::IsNullOrWhiteSpace($mysqlUrl)) {
  if ([string]::IsNullOrWhiteSpace($mysqlHost) -or $mysqlHost -eq "your-host") { $missing += "MYSQLHOST" }
  if ([string]::IsNullOrWhiteSpace($mysqlPort)) { $missing += "MYSQLPORT" }
  if ([string]::IsNullOrWhiteSpace($mysqlDb)) { $missing += "MYSQLDATABASE (or MYSQL_DATABASE)" }
  if ([string]::IsNullOrWhiteSpace($mysqlUser)) { $missing += "MYSQLUSER (or MYSQL_USER)" }
  if ([string]::IsNullOrWhiteSpace($password)) {
    $missing += "MYSQLPASSWORD (or MYSQL_ROOT_PASSWORD)"
  }
}

if ($missing.Count -gt 0) {
  Write-Host "Missing required environment variables: $($missing -join ', ')" -ForegroundColor Red
  Write-Host "Set them first, then run this script again." -ForegroundColor Yellow
  exit 1
}

Write-Host "Running Django migrations on MySQL..." -ForegroundColor Cyan
python mysite/manage.py migrate

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "MySQL migration completed." -ForegroundColor Green
