# Artifact map

This file lists the main public artifacts and how they are used.

## Source inputs

The `inputs/` directory contains source archives needed for staged reproduction:

```text
feedback_v050_h004_local_proof_freeze_main.zip
feedback_v086_true_arb_and_local_tensor_port_v1.zip
feedback_v096_adaptive_full_ledger_rerun_executor.zip
adaptive_full_ledger_export_v096.zip
feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip
feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip
feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip
```

These files should not be edited by hand.

## Certificate files

The `certificate/` directory contains:

```text
feedback_v109_signed_author_self_review.zip
reviewer_signoff_v109.json
MANIFEST.json
SHA256SUMS.txt
```

The final verifier checks these files together with the required inputs and the paper PDF.

## Intermediate reference archives

The `certificate/intermediate/` directory contains reference V106-V108 feedback archives.  They are used for reference-signed verification and for comparison with regenerated stage archives.

## Paper

The `paper/` directory contains the compiled accompanying PDF.

## Figures

The `assets/figures/` directory contains README figures derived from the paper figures.

## Generated outputs

The `runs/` directory is created by the scripts and should not be committed.  It contains logs, summaries, and regenerated feedback archives.

## Integrity files

`certificate/SHA256SUMS.txt` records the SHA256 digest of public repository files included in the verification manifest.  `certificate/MANIFEST.json` records the same inventory in structured JSON form.
