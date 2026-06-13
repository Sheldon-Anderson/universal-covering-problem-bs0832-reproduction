# Verification design

This note connects the mathematical proof obligations to the public verifier modules. The repository verifies a bundled finite certificate. It does not rerun the original geometric search and does not regenerate the certificate records from scratch.

| Obligation group | Mathematical assertion | Certificate records | Public verifier module | Failure condition |
|---|---|---|---|---|
| OB-A | The recorded admissible domain is covered by finitely many parameter domains. | final adjudication records and cover-level proof-obligation rows | `ucbs.certificate.final_adjudication` | missing obligation row, failed obligation status, or final gate blocker |
| OB-B | Supporting domains satisfy local lower bounds at the same certified threshold. | per-record evidence and construction audit records | `ucbs.certificate.per_record_evidence`, `ucbs.certificate.construction_audit` | missing family, empty CSV, failed closure, or malformed schema |
| OB-C | Witness domains satisfy local lower bounds. | witness point, order, determinant, and shoelace records | `ucbs.certificate.witness_construction` | missing accepted subdomain evidence, failed orientation/order, or area lower endpoint below the threshold |
| OB-D | Every used local record has individual evidence. | per-record closure summaries and row-family records | `ucbs.certificate.per_record_evidence` | missing expected family, nonzero blocker count, or non-closed status |
| OB-E | Interval endpoints and rounding records are theorem-relevant and clear the threshold. | construction and witness interval-operation records | `ucbs.certificate.construction_audit`, `ucbs.certificate.witness_construction` | missing rounding rows, unavailable recorded arithmetic backend, or threshold containment failure |
| OB-F | The final aggregation is applied only to the stated convex claim. | final adjudication, claim-boundary, and hash-integrity records | `ucbs.certificate.final_adjudication`, `ucbs.verification.claim_boundary` | over-claim hit, missing final proof-obligation row, or hash-integrity failure |

The public repository check additionally runs README math-rendering lint, clean narrative lint, Python compilation, package metadata checks, layout checks, and artifact hash checks.


## Verification depth

The verifier checks bundled certificate records. It does not rerun the original geometric search and does not regenerate the certificate archives from scratch.

## Failure semantics

A missing expected row, an empty required table, a malformed schema, a duplicate key, a hash mismatch, or a failed check row is a verification failure. Intermediate adaptive-refinement rows are allowed only when the component verifier identifies them as nonterminal records.
