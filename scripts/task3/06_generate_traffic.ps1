# Generates traffic through gateway for metrics and logs.
param(
  [string]$BaseUrl = "http://localhost:8080",
  [int]$Count = 50
)

for ($i=1; $i -le $Count; $i++) {
  try {
    Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing | Out-Null
    Invoke-WebRequest -Uri "$BaseUrl/expenses/health" -UseBasicParsing | Out-Null
  } catch {
    Write-Host "Request failed: $($_.Exception.Message)"
  }
  Start-Sleep -Milliseconds 200
}
