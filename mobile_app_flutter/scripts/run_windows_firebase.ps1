# Launches the Flutter Windows app in Firebase auth preview mode.
# Reads secrets from firebase_android.local.ps1 (git-ignored, not committed).
# Note: same Firebase project values work here since options are passed explicitly, not via a platform config file.

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$localSecrets = Join-Path $repoRoot 'firebase_android.local.ps1'

if (-not (Test-Path $localSecrets)) {
    Write-Error "Missing $localSecrets. Copy firebase_android.local.ps1.example to firebase_android.local.ps1 and fill in real values."
    exit 1
}

. $localSecrets

$required = @(
    'APP_FIREBASE_API_KEY',
    'APP_FIREBASE_APP_ID',
    'APP_FIREBASE_MESSAGING_SENDER_ID',
    'APP_FIREBASE_PROJECT_ID'
)
foreach ($name in $required) {
    if ([string]::IsNullOrWhiteSpace((Get-Item "env:$name" -ErrorAction SilentlyContinue).Value)) {
        Write-Error "Missing required value: $name (set it in firebase_android.local.ps1)"
        exit 1
    }
}

Push-Location $repoRoot
try {
    flutter run -d windows `
        --dart-define=APP_AUTH_MODE=firebase `
        --dart-define=APP_FIREBASE_API_KEY=$env:APP_FIREBASE_API_KEY `
        --dart-define=APP_FIREBASE_APP_ID=$env:APP_FIREBASE_APP_ID `
        --dart-define=APP_FIREBASE_MESSAGING_SENDER_ID=$env:APP_FIREBASE_MESSAGING_SENDER_ID `
        --dart-define=APP_FIREBASE_PROJECT_ID=$env:APP_FIREBASE_PROJECT_ID `
        --dart-define=APP_FIREBASE_STORAGE_BUCKET=$env:APP_FIREBASE_STORAGE_BUCKET `
        --dart-define=APP_FIREBASE_AUTH_DOMAIN=$env:APP_FIREBASE_AUTH_DOMAIN
}
finally {
    Pop-Location
}
