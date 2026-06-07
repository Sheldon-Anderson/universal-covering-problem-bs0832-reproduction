# Artifact map

This file describes the public artifacts used by the BS0832 certificate repository.

## Source inputs

The `inputs/` directory contains the source archives needed for staged reproduction:

```text
feedback_v050_h004_local_proof_freeze_main.zip
feedback_v086_true_arb_and_local_tensor_port_v1.zip
feedback_v096_adaptive_full_ledger_rerun_executor.zip
adaptive_full_ledger_export_v096.zip
feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip
feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip
feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip
```

These ZIP files are certificate inputs. They should not be edited by hand.

## Certificate files

The `certificate/` directory contains:

```text
feedback_v109_signed_author_self_review.zip
reviewer_signoff_v109.json
MANIFEST.json
SHA256SUMS.txt
```

The final verifier checks the v109 archive, validates the author self-review signoff, and compares `MANIFEST.json` with `SHA256SUMS.txt`.

## Intermediate reference archives

The `certificate/intermediate/` directory contains the reference V106-V108 feedback archives. They are used by the reference-signed path and for comparison with locally regenerated stage archives.

```text
feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip
feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip
feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip
```

## Manifest policy

In v0.12 the manifest is a **certificate-artifact manifest**, not a whole-repository manifest. The checksum gate covers only:

```text
inputs/*.zip
certificate/intermediate/*.zip
certificate/feedback_v109_signed_author_self_review.zip
certificate/reviewer_signoff_v109.json
```

Documentation, figures, the compiled paper, CI files, and Python source files are intentionally outside this certificate-artifact checksum gate. They may be revised without changing the artifact hashes.

## Paper and figures

The `paper/` directory contains the compiled accompanying manuscript PDF. The `assets/figures/` directory contains figures used by the README files. These files are distributed for exposition and are not part of the certificate-artifact SHA256 gate.

## Generated outputs

The `runs/` directory is created by the verification scripts. It contains logs, JSON summaries, and regenerated feedback archives. It should not be committed to the repository.
