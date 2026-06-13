# Data dictionary

This document explains the main JSON and CSV fields written by the public verification commands. See `docs/expected_outputs.md` for output file paths.

## Common status fields

| Field | Meaning |
|---|---|
| `status` | `passed` when the command succeeds. |
| `certified_threshold` | The exact decimal threshold used by the public replay, currently `0.83201`. |
| `threshold_proved` | Boolean summary that the checked certificate records establish the certified threshold. |
| `failed_component_count` | Number of failed certificate-chain components. |

## Main certificate verification

| Field | Meaning |
|---|---|
| `certificate_verified` | Boolean summary for the bundled finite certificate. |
| `component_count` | Number of certificate-chain components checked. |
| `per_record_evidence_passed` | Component status for individual evidence closure. |
| `construction_audit_passed` | Component status for construction and rounding records. |
| `witness_construction_passed` | Component status for witness-domain records. |
| `final_adjudication_passed` | Component status for final proof-obligation and claim-boundary records. |

## Per-record evidence replay

| Field | Meaning |
|---|---|
| `closure_rows` | Number of closure-summary records checked. |
| `failed_rows` | Number of evidence-closure failures. The expected value is `0`. |
| `selected_row_count_total` | Number of selected source rows represented by the closure records. |

## Construction audit replay

| Field | Meaning |
|---|---|
| `artifact_rows` | Number of artifact audit rows. |
| `candidate_polygon_rows` | Number of candidate polygon records checked in the construction component. |
| `operation_rows` | Number of operation-level rounding records checked. |
| `support_to_area_rows` | Number of support-to-area records checked. |
| `construction_audit_passed` | Boolean component status. |

## Witness construction replay

| Field | Meaning |
|---|---|
| `witness_domains` | Number of witness domains. |
| `accepted_terminal_subdomains` | Number of terminal witness subdomains accepted by the witness construction records. |
| `failed_terminal_subdomains` | Number of unresolved terminal witness subdomains. The expected value is `0`. |
| `intermediate_split_rows_ignored_as_nonterminal` | Adaptive refinement rows that are not terminal certificate failures. |
| `point_containment_passed` | Whether witness point containment records pass. |
| `orientation_certificates_passed` | Whether orientation estimates for accepted terminal subdomains pass. |
| `shoelace_lower_bounds_passed` | Whether shoelace lower bounds clear the certified threshold. |

## Final adjudication replay

| Field | Meaning |
|---|---|
| `certificate_verified` | Whether the final finite certificate record is accepted. |
| `proof_obligations_discharged` | Whether the final proof-obligation records are discharged. |
| `nonconvex_lower_bound_claimed` | Scope flag; expected value is `false`. |
| `proof_assistant_formalization_completed` | Scope flag; expected value is `false`. |
| `independent_external_verification_completed` | Scope flag; expected value is `false`. |

## Diagnostics CSV files

All diagnostic CSV files contain a stable header and either issue rows or a summary row. A row with `passed=false` contributes to command failure. Empty successful checks still write a summary row so that users can distinguish a successful check from a missing file.
