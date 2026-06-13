# Certificate archive structure

This page explains the relationship between public archive names and raw certificate-record names.

## Public archives

| Public component | Public archive | Purpose |
|---|---|---|
| per-record evidence | `certificate/final_chain/per_record_evidence_feedback.zip` | Checks that supporting local records are tied to individual evidence records. |
| construction audit | `certificate/final_chain/construction_audit_feedback.zip` | Checks construction-stage artifacts, rounding records, and support-to-area records. |
| witness construction | `certificate/final_chain/witness_construction_feedback.zip` | Checks witness point containment, cyclic-order evidence, orientation estimates, and shoelace lower bounds. |
| final adjudication | `certificate/final_chain/final_adjudication_feedback.zip` | Checks final proof obligations, claim-boundary records, and scope flags. |

## Raw internal record families

Some files inside the archives preserve internal identifiers such as v133, v134, v135, and v136. These labels identify raw certificate-record families and are retained only for provenance. They are not public release versions, not user-facing commands, and not separate mathematical claims.

| Internal family | Public role |
|---|---|
| raw v133 family | per-record evidence closure |
| raw v134 family | construction audit, rounding records, and support-to-area checks |
| raw v135 family | witness construction, orientation estimates, and shoelace lower bounds |
| raw v136 family | final adjudication and claim-boundary checks |

## Replay depth

The public verifier replays theorem-relevant checks from these bundled archives. It does not run a search program to discover new certificate records, and it does not regenerate the archives from the original geometric search.

## Raw internal field names

The public archive names are stable. Some raw CSV/JSON records inside the archives preserve generation-stage identifiers for provenance. Raw fields such as `candidate_only` and `theorem_ready` should be interpreted through the public verifier outputs. The stable public status fields are `certificate_verified`, `threshold_proved`, and the component flags reported in `runs/*/status/*.json`.

See `certificate/public/CERTIFICATE_INDEX.md` and `docs/verification_design.md` for the mapping from public components to raw record families and proof-obligation groups.
