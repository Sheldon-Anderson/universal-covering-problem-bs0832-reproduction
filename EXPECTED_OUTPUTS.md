# Expected outputs

This file gives a compact checklist for interpreting the public verification commands.

## Final repository verification

Command:

```bash
python -m scripts.run_final_verification --root . --log-level INFO
```

Output files:

```text
runs/final_verification/final_verification_summary.json
runs/final_verification/final_verification.log
```

A successful run reports these key fields in `final_verification_summary.json`:

```text
status = success
bs0832_final_repository_verification_passed = true
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

It also records a signoff summary with:

```text
accepted_obligations = 19
accepted_gaps = 4
```

The value `theorem_ready=false` is expected.  It records that the public repository is an author-reviewed reproducible certificate package and not a proof-assistant formalization.

## Full staged reproduction

Command:

```bash
python -m scripts.run_all_stages --root . --log-level INFO
```

Top-level output:

```text
runs/stage_all/stage_chain_summary.json
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

The reference-signed V109 run validates the bundled signoff against the reference V108 archive.  The generated-chain V109 run uses the freshly generated V108-style archive and does not automatically inherit the bundled author signoff.

## Byte-level ZIP differences

A regenerated ZIP archive may have a different SHA256 hash from the bundled reference ZIP because ZIP metadata such as timestamps, compression settings, and file ordering can differ.  Stage summaries therefore report generated and reference hashes for traceability, but byte-for-byte equality is not the sole acceptance criterion.
