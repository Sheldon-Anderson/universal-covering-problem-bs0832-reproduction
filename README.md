# Lebesgue Universal Cover - Certified Lower-Bound Certificate

This repository contains a finite certificate and Python verification code for the certified threshold

$$
\tau = 0.83201
$$

in the convex Brass-Sharifi three-test-set lower-bound framework for Lebesgue's universal cover problem.
The result verified here is the convex certificate consequence

$$
\alpha_{\mathrm{cvx}} \ge 0.83201.
$$

The repository includes the certificate-chain archives needed for local verification. No extra certificate data download is required.

## Contents

- [What this repository verifies](#1-what-this-repository-verifies)
- [Background and scope](#2-background-and-scope)
- [Proof idea](#3-proof-idea)
- [What is included](#4-what-is-included)
- [Quick start](#5-quick-start)
- [Installation](#6-installation)
- [Main certificate verification](#7-main-certificate-verification)
- [Repository check](#8-repository-check)
- [Full certificate-chain replay](#9-full-certificate-chain-replay)
- [Advanced component replay commands](#10-advanced-component-replay-commands)
- [Expected outputs](#11-expected-outputs)
- [Artifact and SHA256 policy](#12-artifact-and-sha256-policy)
- [Troubleshooting](#13-troubleshooting)
- [FAQ](#14-faq)
- [Paper, citation, and license](#15-paper-citation-and-license)

## 1. What this repository verifies

Let $\mathcal{U}_{\mathrm{cvx}}$ be the class of convex universal covers and set

$$
\alpha_{\mathrm{cvx}}
=
\inf_{K\in\mathcal{U}_{\mathrm{cvx}}}\mathrm{area}(K).
$$

The certificate verifies that every normalized placement in the Brass-Sharifi convex three-test-set framework has hull area at least $\tau=0.83201$. The finite-cover implication then gives $\alpha_{\mathrm{cvx}}\ge0.83201$.

The statement is limited to the convex Brass-Sharifi three-test-set certificate setting. It does not claim a result for the unrestricted nonconvex problem, a proof-assistant formalization, or completed independent external verification.

## 2. Background and scope

Lebesgue's universal cover problem asks for a planar set of least possible area that contains a congruent copy of every planar set of diameter one. In the convex setting, the covering set is required to be convex.

The Brass-Sharifi framework uses three necessary test sets of diameter one: a disk $C$, an equilateral triangle $T$, and a regular pentagon $P_5$. A convex universal cover must contain congruent copies of all three. Convexity then forces the cover to contain the convex hull of those copies.

This repository verifies a finite certificate for the lower bound in that normalized convex framework. It is not a search engine for new certificates; it checks the bundled certificate records.

## 3. Proof idea

The proof is organized as a chain of finite mathematical checks.

### Step 1. From a convex universal cover to a three-test-set hull

If $K\in\mathcal{U}_{\mathrm{cvx}}$, then $K$ contains congruent copies of $C$, $T$, and $P_5$. Since $K$ is convex, it contains their convex hull.

### Step 2. From normalized placements to the hull-area function

A normalized placement is

$$
v=(\rho,x_3,y_3,x_5,y_5),\qquad
u_3=(x_3,y_3),\qquad
u_5=(x_5,y_5).
$$

With $R_\rho$ denoting rotation by angle $\rho$, set

$$
X(v)=C\cup(T+u_3)\cup(R_\rho P_5+u_5),
\qquad
H(v)=\mathrm{conv}(X(v)),
\qquad
A(v)=\mathrm{area}(H(v)).
$$

Thus a lower bound for $A(v)$ on the admissible normalized domain gives a lower bound for the area of every convex universal cover.

### Step 3. From the admissible domain to a finite cover

The certificate verifies a finite family $\mathcal F$ such that

$$
\Omega_{\mathrm{adm}}\subseteq\bigcup_{B\in\mathcal F}B.
$$

For each domain $B\in\mathcal F$, the certificate supplies a local lower bound $L_B$ and verifies

$$
A(v)\ge L_B\ge\tau
\qquad (v\in B).
$$

### Step 4. From witness points to witness-domain lower bounds

On the witness domains, the certificate gives points $Q_B(v)\subseteq X(v)$. Therefore

$$
W_B(v)=\mathrm{conv}(Q_B(v))\subseteq H(v),
$$

so $A(v)\ge\mathrm{area}(W_B(v))$. The verifier checks witness containment, a certified cyclic order, and shoelace lower endpoints using outward-rounded interval arithmetic.

### Step 5. From local inequalities to the convex lower bound

Since every admissible parameter lies in some $B\in\mathcal F$, the local inequalities imply

$$
A(v)\ge0.83201\qquad(v\in\Omega_{\mathrm{adm}}).
$$

The convex universal-cover consequence is $\alpha_{\mathrm{cvx}}\ge0.83201$.

## 4. What is included

| Path | Purpose |
|---|---|
| `certificate/final_chain/` | Four bundled certificate-chain archives used by the verifier. |
| `certificate/manifest/` | SHA256 manifest for certificate-chain archives. |
| `certificate/public/` | Human-readable certificate status and claim-boundary notes. |
| `ucbs/certificate/` | Python modules that replay certificate-critical checks from the archives. |
| `ucbs/verification/` | Repository-release checks: README math rendering, claim boundary, layout, hashes, and source checks. |
| `scripts/` | Public command-line entry points. |
| `docs/` | Reproducibility, expected outputs, artifact policy, and FAQ. |
| `paper/` | Compiled paper preview. |

The four certificate-chain archives are:

```text
certificate/final_chain/per_record_evidence_feedback.zip
certificate/final_chain/construction_audit_feedback.zip
certificate/final_chain/witness_construction_feedback.zip
certificate/final_chain/final_adjudication_feedback.zip
```

## 5. Quick start

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python scripts/verify_certificate.py --root . --log-level INFO
python scripts/check_repository.py --root . --log-level INFO
```

A successful main verification writes:

```text
runs/certificate_verification/status/certificate_verification.status.json
runs/certificate_verification/log/certificate_verification.log
```

The expected core fields are:

```json
{
  "status": "passed",
  "certificate_verified": true,
  "threshold_proved": true,
  "certified_threshold": "0.83201",
  "failed_component_count": 0
}
```

## 6. Installation

Requirements:

- Python 3.10 or later.
- Dependencies listed in `requirements.txt`.
- No GPU is required.

Recommended environment setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

Windows PowerShell activation is:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 7. Main certificate verification

Command:

```bash
python scripts/verify_certificate.py --root . --log-level INFO
```

Function:

- Reads the four archives in `certificate/final_chain/`.
- Replays the per-record evidence, construction audit, witness construction, and final adjudication components.
- Writes detailed logs, diagnostic CSV files, and a status JSON file.

Outputs:

```text
runs/certificate_verification/status/certificate_verification.status.json
runs/certificate_verification/diagnostics/component_checks.csv
runs/certificate_verification/diagnostics/failed_component_checks.csv
runs/certificate_verification/log/certificate_verification.log
runs/certificate_verification/certificate_verification_feedback.zip
```

Explicit archive paths can be supplied when needed:

```bash
python scripts/verify_certificate.py \
  --root . \
  --per-record-evidence-zip certificate/final_chain/per_record_evidence_feedback.zip \
  --construction-audit-zip certificate/final_chain/construction_audit_feedback.zip \
  --witness-construction-zip certificate/final_chain/witness_construction_feedback.zip \
  --final-adjudication-zip certificate/final_chain/final_adjudication_feedback.zip \
  --log-level INFO
```

## 8. Repository check

Command:

```bash
python scripts/check_repository.py --root . --log-level INFO
```

Function:

- Checks Python compilation and package metadata.
- Checks repository layout and empty directories.
- Checks public Markdown math rendering.
- Checks claim-boundary wording.
- Checks clean public narrative wording.
- Checks SHA256 hashes for certificate-chain archives.
- Runs the main certificate verification internally.

Outputs:

```text
runs/repository_check/status/repository_check.status.json
runs/repository_check/diagnostics/failed_checks.csv
runs/repository_check/diagnostics/readme_math.csv
runs/repository_check/diagnostics/narrative_lint.csv
runs/repository_check/diagnostics/claim_boundary.csv
runs/repository_check/diagnostics/artifact_hashes.csv
runs/repository_check/log/repository_check.log
runs/repository_check/repository_check_feedback.zip
```

Because this command runs the main certificate verification internally, it also creates:

```text
runs/certificate_verification/
```

Expected status:

```json
{
  "status": "passed",
  "failed_step_count": 0
}
```

## 9. Full certificate-chain replay

Command:

```bash
python scripts/replay_certificate_chain.py --root . --log-level INFO
```

Function:

- Replays the four certificate-chain components.
- Does not run repository-release checks such as README lint or claim-boundary lint.
- Is useful when a reader wants to inspect the mathematical certificate chain without auditing the whole release package.

Outputs:

```text
runs/certificate_chain_replay/status/certificate_chain_replay.status.json
runs/certificate_chain_replay/diagnostics/component_checks.csv
runs/certificate_chain_replay/log/certificate_chain_replay.log
runs/certificate_chain_replay/certificate_chain_replay_feedback.zip
```

Expected fields:

```json
{
  "status": "passed",
  "per_record_evidence_passed": true,
  "construction_audit_passed": true,
  "witness_construction_passed": true,
  "final_adjudication_passed": true,
  "failed_component_count": 0
}
```

## 10. Advanced component replay commands

These commands inspect individual components. They do not replace the main certificate verification.

### 10.1 Per-record evidence

```bash
python scripts/replay_per_record_evidence.py --root . --log-level INFO
```

Reads `certificate/final_chain/per_record_evidence_feedback.zip` and checks that supporting local records are tied to individual evidence rows. Expected fields include `status = passed` and `failed_rows = 0`.

### 10.2 Construction audit

```bash
python scripts/replay_construction_audit.py --root . --log-level INFO
```

Reads `certificate/final_chain/construction_audit_feedback.zip` and checks construction-stage artifacts, rounding rows, and integrity rows. Expected fields include `status = passed` and `construction_audit_passed = true`.

### 10.3 Witness construction

```bash
python scripts/replay_witness_construction.py --root . --log-level INFO
```

Reads `certificate/final_chain/witness_construction_feedback.zip` and checks witness containment, accepted terminal subdomains, orientation rows, and shoelace lower bounds. Expected fields include `status = passed`, `witness_construction_passed = true`, and `accepted_terminal_subdomains = 140`.

### 10.4 Final adjudication

```bash
python scripts/replay_final_adjudication.py --root . --log-level INFO
```

Reads `certificate/final_chain/final_adjudication_feedback.zip` and checks the final finite certificate conditions, proof obligations, claim-boundary rows, and scope flags. Expected fields include `status = passed` and `threshold_proved = true`.

## 11. Expected outputs

The most important files are:

| File | Meaning |
|---|---|
| `runs/certificate_verification/status/certificate_verification.status.json` | Main certificate verification status. |
| `runs/certificate_verification/diagnostics/component_checks.csv` | Four-component replay summary. |
| `runs/repository_check/status/repository_check.status.json` | Public release check status. |
| `runs/repository_check/diagnostics/failed_checks.csv` | Failed repository diagnostics, or a summary row when none fail. |
| `runs/certificate_chain_replay/status/certificate_chain_replay.status.json` | Certificate-chain-only replay status. |

Every diagnostic CSV is written with a header and a summary row, including the no-issue case.

## 12. Artifact and SHA256 policy

The SHA256 gate covers certificate-chain archives in `certificate/final_chain/`. These archives are the certificate data used by the replay code. Documentation files, paper files, and Python source files are checked by repository diagnostics and release control rather than by the certificate-data hash gate.

The manifest is:

```text
certificate/manifest/key_artifacts_sha256.txt
```

To inspect the manifest:

```bash
cat certificate/manifest/key_artifacts_sha256.txt
```

## 13. Troubleshooting

### Dependency installation fails

Upgrade `pip` and retry:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### A certificate archive is missing

Check that the four files listed in Section 4 exist under `certificate/final_chain/`.

### Main verification fails

Open:

```text
runs/certificate_verification/log/certificate_verification.log
runs/certificate_verification/diagnostics/failed_component_checks.csv
```

### Repository check fails

Open:

```text
runs/repository_check/diagnostics/failed_checks.csv
runs/repository_check/log/repository_check.log
```

### README math rendering fails

Use `$...$` for inline math and `$$...$$` for display math in public Markdown. The repository check deliberately rejects `\(...\)` and `\[...\]` in public Markdown files.

## 14. FAQ

### Does this repository include all certificate data needed for verification?

Yes. The required archives are bundled in `certificate/final_chain/`.

### Does this prove the unrestricted nonconvex problem?

No. The verified statement is the convex Brass-Sharifi three-test-set certificate consequence.

### Is this a proof-assistant formalization?

No. The repository provides a finite certificate and deterministic Python replay checks. It does not claim a Lean, Coq, Isabelle, or other proof-assistant formalization.

### Why is the minimum witness-domain area bound larger than 0.83201?

The witness-domain minimum is local to the domains handled by the witness construction. The global certified threshold is the minimum guaranteed after all local records over the full finite cover are combined.

## 15. Paper, citation, and license

The compiled paper preview is in `paper/`.

Citation metadata is provided in `CITATION.cff`.

This repository is released under the MIT license. See `LICENSE`.
