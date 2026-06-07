# Certificate structure

This repository organizes the Brass-Sharifi 0.832 computation as a finite certificate package for the convex universal-cover lower bound.

## Placement-level statement

The certificate concerns the normalized three-test-set placement problem. With

$$
v=(\rho,x_3,y_3,x_5,y_5),
\qquad
u_3=(x_3,y_3),
\qquad
u_5=(x_5,y_5),
$$

and

$$
H(v)=\operatorname{conv}\left(C\cup(T+u_3)\cup(R_\rho P_5+u_5)\right),
\qquad
A(v)=\operatorname{area}(H(v)),
$$

the placement-level statement represented by the certificate is

$$
A(v)\geq 0.832
$$

for every admissible normalized placement recorded by the certificate domain model.

## Domain route

The certificate uses the Branch-B enlarged-domain route:

$$
\Omega_{\mathrm{adm}} \subseteq \Omega_B
\subseteq \bigcup_{r\in\mathcal R}\Omega_r.
$$

Branch-A is an internal label for a symbolic domain-reduction route that is not claimed closed in this repository. All public certificate claims use Branch-B.

## Certificate layers

The public certificate has four main layers.

1. **Adaptive ledger.** A finite parent-child subdivision ledger records the recursive search tree and its terminal routes.
2. **Route dispatch.** Every terminal route is assigned to exactly one local certificate family.
3. **Local certificate families.** The three families are directed interval certificates, local tensor certificates, and the \(h=0.004\) bridge.
4. **Proof-obligation and signoff layer.** Nineteen obligations, grouped as OB-A through OB-F, connect the replayed data to the final 0.832 statement.

## Local certificate interface

For each accepted terminal route \(r\), the local record supplies a post-guard lower-bound certificate through the interface

$$
L^{\mathrm{post}}_r \leq \inf_{w\in\Omega_r} A(w),
\qquad
L^{\mathrm{post}}_r - 0.832 \geq 10^{-7}.
$$

Therefore the accepted route supplies

$$
A(v)\geq 0.832,
\qquad v\in\Omega_r.
$$

The directed interval and local tensor records use a post-guard margin threshold of \(10^{-7}\) above 0.832. The bridge family covers the small residual route set through frozen witness records.

## Stage labels

| Stage | Role |
|---|---|
| V106 | Branch-B domain replay and kernel-closure checks |
| V107 | independent replay and compact hash audits |
| V108 | reproduction closure and artifact-to-obligation binding |
| V109 | final signoff adjudication and author self-review validation |

The labels are repository stage names. They are not theorem numbers.

## Reference-signed and generated-chain modes

The final signed-candidate certificate is bound to the reference V108 archive reviewed in `certificate/reviewer_signoff_v109.json`. This is the `reference-signed` path used by quick final verification.

The `generated-chain` path reruns the construction pipeline and can produce a fresh V108-style archive. A freshly generated ZIP may be logically equivalent but bytewise different. It does not automatically inherit the author signoff attached to the reference V108 archive.

## Current proof boundary

The repository deliberately preserves the following boundary:

```text
theorem_ready = false
```

This means the public repository is a reproducible certificate package with author self-review. It does not claim proof-assistant formalization, independent external review, Branch-A closure, a nonconvex lower bound, or a stronger numerical lower-bound claim.
