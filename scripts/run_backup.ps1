Param(
    [Parameter(Mandatory=$false, HelpMessage = "The environment to run the app (dev, prod)")]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "prod"
)

if ( -Not ( Get-Command "uv" ) ) {
    Write-Error "uv is not installed."
    exit 1
}

if ( $Environment -eq "dev" ) {
    $env:ENV_FOR_DYNACONF="dev"
} else {
    $env:ENV_FOR_DYNACONF="prod"
}

Write-Host "Running app in $Environment mode"

try {
    uv run src\auto_sftp
} catch {
    Write-Error "Error running auto_sftp script. Details: $($_.Exception.Message)"
    exit 1
}

Write-Host "Finished SFTP synch." -ForegroundColor Green

exit 0
