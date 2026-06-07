# Expected outputs

This file gives a compact checklist for interpreting the public verification commands.

## Final repository verification

Command:

```bash
python -m scripts.run_final_verification --root . --log-level INFO
```

Purpose: check the bundled reference certificate artifacts, the certificate-only manifest/SHA256 gate, the final signed-candidate archive, and the structured author self-review signoff.

Output files:

```text
runs/final_verification/final_verification_summary.json
runs/final_verification/final_verification.log
```

A successful run reports these key fields in `final_verification_summary.json`:

```text
status = success
bs0832_final_repository_verification_passed = true
required_file_count = 14
sha256_checked_file_count = 12
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

The field `required_file_count = 14` counts the seven source input ZIPs, the three intermediate reference ZIPs, and the four final certificate files under `certificate/`.

The field `sha256_checked_file_count = 12` counts only certificate artifacts in the v0.12 checksum gate:

```text
inputs/*.zip
certificate/intermediate/*.zip
certificate/feedback_v109_signed_author_self_review.zip
certificate/reviewer_signoff_v109.json
```

Documentation, figures, the paper PDF, CI configuration, and Python source comments are intentionally outside this artifact-level SHA gate.

The successful run also records a signoff summary with:

```text
accepted_obligations = 19
accepted_gaps = 4
```

The value `theorem_ready=false` is expected. It records that the public repository is an author-reviewed reproducible certificate package and not a proof-assistant formalization.

## Full staged reproduction

Command:

```bash
python -m scripts.run_all_stages --root . --log-level INFO
```

Purpose: run the public staged chain V106, V107, V108, V109 reference-signed, and V109 generated-chain.

Top-level output:

```text
runs/stage_all/stage_chain_summary.json
runs/stage_all/public_stage_chain.log
```

Expected stage directories:

```text
runs/stage_v106/
runs/stage_v107/
runs/stage_v108/
runs/stage_v109_reference/
runs/stage_v109_generated/
```

A successful staged chain reports:

```text
status = success
```

The reference-signed V109 run validates the bundled signoff against the reference V108 archive. The generated-chain V109 run uses the freshly generated V108-style archive and does not automatically inherit the bundled author signoff.

## Single-stage commands

V106:

```bash
python -m scripts.run_stage_v106 --root . --log-level INFO
```

Expected output: `runs/stage_v106/` with a feedback ZIP, summary JSON, and log file.

V107:

```bash
python -m scripts.run_stage_v107 --root . --log-level INFO
```

Expected output: `runs/stage_v107/` with a feedback ZIP, summary JSON, and log file. This is usually the heaviest stage.

V108:

```bash
python -m scripts.run_stage_v108 --root . --log-level INFO
```

Expected output: `runs/stage_v108/` with a feedback ZIP, summary JSON, and log file.

V109 reference-signed:

```bash
python -m scripts.run_stage_v109 --root . --mode reference-signed --log-level INFO
```

Expected output: `runs/stage_v109_reference/` with a V109 summary and log.

V109 generated-chain:

```bash
python -m scripts.run_stage_v109 --root . --mode generated-chain \
  --v108-feedback-zip runs/stage_v108/feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip \
  --log-level INFO
```

Expected output: `runs/stage_v109_generated/` with a V109 summary and log.

## Byte-level ZIP differences

A regenerated ZIP archive may have a different SHA256 hash from the bundled reference ZIP because ZIP metadata such as timestamps, compression settings, and file ordering can differ. Stage summaries therefore report generated and reference hashes for traceability, but byte-for-byte equality is not the sole acceptance criterion.
