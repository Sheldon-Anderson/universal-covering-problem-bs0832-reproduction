# Certificate structure

This repository organizes the Brass-Sharifi `0.832` computation as a finite certificate chain.

## Mathematical statement

The placement-level statement checked by the certificate is

```text
A(v) >= 0.832
```

for all admissible normalized placements of the disk, equilateral triangle, and regular pentagon used in the Brass-Sharifi three-test-set route.  The accompanying paper explains how this placement statement implies the convex universal-cover lower bound.

## Certificate layers

The public certificate has four main layers.

1. **Adaptive ledger.** A finite parent-child subdivision ledger records the recursive search tree and its terminal routes.
2. **Route dispatch.** Every terminal route is assigned to one of three local certificate families.
3. **Local certificate families.** The three families are directed interval certificates, local tensor certificates, and the `h=0.004` bridge.
4. **Proof-obligation and signoff layer.** Nineteen obligations, grouped as OB-A through OB-F, connect the replayed data to the final `0.832` statement.

## Stage labels

| Stage | Role |
|---|---|
| V106 | Branch-B domain replay and kernel-closure checks |
| V107 | independent replay and compact hash audits |
| V108 | reproduction closure and artifact-to-obligation binding |
| V109 | final signoff adjudication and author self-review validation |

The labels are repository stage names, inherited from development versions v0.10.6-v0.10.9.  They are not theorem numbers.

## Reference-signed and generated-chain modes

The final signed-candidate certificate is bound to the reference V108 archive reviewed in `certificate/reviewer_signoff_v109.json`.  This is the `reference-signed` path.

The `generated-chain` path reruns the construction pipeline.  It can produce a fresh V108-style archive and run V109 on it, but it does not automatically inherit the author signoff attached to the reference V108 archive.

## Current proof boundary

The repository deliberately preserves the following boundary:

```text
theorem_ready = false
```

This means the public repository is a reproducible certificate package with author self-review.  It does not claim a proof-assistant formalization, independent external review, Branch-A closure, or any stronger numerical lower-bound claim.
