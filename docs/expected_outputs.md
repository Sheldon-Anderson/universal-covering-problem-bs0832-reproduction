# Expected outputs

This file lists the main output locations. Field meanings are defined in `docs/data_dictionary.md`.

## Main certificate verification

Command:

```bash
python scripts/verify_certificate.py --root . --log-level INFO
```

Outputs:

```text
runs/certificate_verification/status/certificate_verification.status.json
runs/certificate_verification/diagnostics/component_checks.csv
runs/certificate_verification/diagnostics/failed_component_checks.csv
runs/certificate_verification/log/certificate_verification.log
runs/certificate_verification/certificate_verification_feedback.zip
```

Expected status:

```json
{
  "status": "passed",
  "certificate_verified": true,
  "threshold_proved": true,
  "certified_threshold": "0.83201",
  "failed_component_count": 0
}
```

## Repository check

Command:

```bash
python scripts/check_repository.py --root . --log-level INFO
```

Outputs:

```text
runs/repository_check/status/repository_check.status.json
runs/repository_check/diagnostics/failed_checks.csv
runs/repository_check/diagnostics/readme_math.csv
runs/repository_check/diagnostics/narrative_lint.csv
runs/repository_check/diagnostics/artifact_hashes.csv
runs/repository_check/log/repository_check.log
runs/repository_check/repository_check_feedback.zip
```

Expected status:

```json
{
  "status": "passed",
  "failed_step_count": 0
}
```

## Component-level verification

Each component command writes `status`, `diagnostics`, `log`, and a feedback zip under its own run directory:

```text
runs/per_record_evidence_replay/
runs/construction_audit_replay/
runs/witness_construction_replay/
runs/final_adjudication_replay/
```

For detailed command usage, see `docs/reproducibility.md`.
