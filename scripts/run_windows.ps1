param(
  [ValidateSet("final", "all", "v106", "v107", "v108", "v109")]
  [string]$Mode = "final",
  [string]$Root = ".",
  [string]$LogLevel = "INFO",
  [ValidateSet("reference-signed", "generated-chain")]
  [string]$V109Mode = "reference-signed"
)

switch ($Mode) {
  "final" { python -m scripts.run_final_verification --root $Root --log-level $LogLevel }
  "all"   { python -m scripts.run_all_stages --root $Root --log-level $LogLevel }
  "v106"  { python -m scripts.run_stage_v106 --root $Root --log-level $LogLevel }
  "v107"  { python -m scripts.run_stage_v107 --root $Root --log-level $LogLevel }
  "v108"  { python -m scripts.run_stage_v108 --root $Root --log-level $LogLevel }
  "v109"  { python -m scripts.run_stage_v109 --root $Root --mode $V109Mode --log-level $LogLevel }
}
