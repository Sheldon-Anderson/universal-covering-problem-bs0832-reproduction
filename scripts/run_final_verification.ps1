param(
  [string]$Root = ".",
  [string]$OutputDir = "runs/final_verification",
  [string]$LogLevel = "INFO"
)

python -m scripts.run_final_verification `
  --root $Root `
  --output-dir $OutputDir `
  --log-level $LogLevel
