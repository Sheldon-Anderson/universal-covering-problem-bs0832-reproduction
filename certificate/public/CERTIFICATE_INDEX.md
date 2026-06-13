# Certificate index

The certificate chain consists of four public archives. The internal record names inside the archives preserve generation-stage identifiers for provenance. The public verifier maps those raw records into stable public components.

| Public component | Public archive | Raw internal family | Main diagnostic records | Expected public invariant | Verifier module |
|---|---|---|---|---|---|
| per-record evidence | `per_record_evidence_feedback.zip` | raw v133 evidence-closure family | `v133_row_level_evidence_closure_summary.csv` and row-family closure tables | 3 closure families, no failed rows, positive selected row count | `ucbs.certificate.per_record_evidence` |
| construction audit | `construction_audit_feedback.zip` | raw v134 construction family | artifact audit, support-to-area rows, candidate polygon rows, operation-level rounding rows | 47 artifact rows, 16 support rows, 16 candidate polygon rows, 96 operation rows | `ucbs.certificate.construction_audit` |
| witness construction | `witness_construction_feedback.zip` | raw v135 witness family | point-containment, orientation, shoelace, order audit, rounding ledger | 16 witness domains, 140 accepted terminal subdomains, zero final unresolved terminal subdomains | `ucbs.certificate.witness_construction` |
| final adjudication | `final_adjudication_feedback.zip` | raw v136 final-adjudication family | final gate, proof obligations, claim-boundary lint, integrity, status consistency | threshold proved, proof obligations discharged, no nonconvex/proof-assistant/external-verification overclaim | `ucbs.certificate.final_adjudication` |

Some raw files include raw generation-stage field names such as `candidate_only` or `theorem_ready`. These fields are kept because they are part of the provenance of the bundled certificate records. The public status records use stable names such as `certificate_verified`, `threshold_proved`, and `witness_construction_passed`.
