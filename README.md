# A Certified Lower Bound for Lebesgue's Universal Cover Problem

This repository contains the finite certificate records and deterministic Python verifier for a certified lower bound in the convex Brass-Sharifi three-test-set framework.

The repository is a verification package for bundled certificate records. It is not a program for rerunning the original geometric search or regenerating the certificate records from scratch.

## 1. Verified statement

The bundled finite certificate verifies the threshold $\tau=0.83201$ for the normalized Brass-Sharifi three-test-set lower-bound problem. Together with the Brass-Sharifi normalization principle, this gives the convex certificate consequence

```math
\alpha_{\mathrm{cvx}} \ge 0.83201.
```

Here $\alpha_{\mathrm{cvx}}$ is the infimum of the areas of convex universal covers. The proof uses a finite cover of the admissible normalized placement domain, supporting local records, witness-domain polygon records, outward-rounded interval estimates, and a final aggregation check.

## 2. Scope

Claimed:

- a finite-certificate verification of $\tau=0.83201$ in the convex Brass-Sharifi three-test-set certificate setting;
- a convex certificate consequence for $\alpha_{\mathrm{cvx}}$;
- deterministic replay of theorem-relevant checks from the bundled certificate records.

Not claimed:

- a result for the unrestricted nonconvex problem;
- a proof-assistant formalization;
- completed independent external verification;
- a rerun of the original geometric search or a regeneration of the certificate archives.

## 3. What is included

| Path | Purpose |
|---|---|
| `certificate/final_chain/` | Four bundled certificate-chain archives. |
| `certificate/manifest/` | SHA256 manifests and manual checksum notes. |
| `certificate/public/CERTIFICATE_INDEX.md` | Public index of certificate components and proof-obligation roles. |
| `ucbs/` | Python package root for the universal-cover Brass-Sharifi certificate verifier. |
| `scripts/` | Stable command-line entry points. |
| `tests/` | Optional developer regression tests for the verifier and lint rules. |
| `docs/` | Reproducibility, output fields, data dictionary, artifact policy, and claim scope. |
| `paper/` | Compiled paper PDF. |

The required certificate data are already bundled with the repository. No additional certificate data download is needed for the public verification commands.

### Key terms

| Term | Meaning |
|---|---|
| finite certificate | Finite records used to verify the certified lower bound. |
| certificate verification | Deterministic replay of the bundled certificate records. |
| witness construction | Witness-domain polygonal lower-bound records. |
| construction audit | Support-to-area and interval-rounding checks. |
| final adjudication | Final proof-obligation and claim-boundary checks. |

## 4. Mathematical proof map

The proof map is:

1. A convex universal cover contains congruent copies of the disk, equilateral triangle, and regular pentagon of diameter one.
2. The Brass-Sharifi normalization represents the corresponding three-test-set hull by a parameter $v$ in the recorded admissible domain $\Omega_{\mathrm{adm}}$.
3. The finite certificate verifies a finite cover of $\Omega_{\mathrm{adm}}$ by parameter domains.
4. Each parameter domain carries a local lower-bound assertion. Supporting domains use supporting local records; witness domains use ordered witness polygons and interval shoelace lower bounds.
5. The final aggregation gives $A(v)\ge 0.83201$ throughout $\Omega_{\mathrm{adm}}$, and the convex consequence follows.

The certificate-chain replay verifies records already bundled in `certificate/final_chain/`. It does not search for new certificates.

## 5. Quick verification

Run the repository check directly from the unpacked source tree:

```bash
python scripts/check_repository.py --root . --log-level INFO
```

A successful repository check also runs the main certificate verification internally. No editable installation is required for the `python scripts/...` commands.

## 6. Main commands

### 6.1 Certificate verification

```bash
python scripts/verify_certificate.py --root . --log-level INFO
```

Purpose: verify the four bundled certificate-chain archives and write the main certificate status under `runs/certificate_verification/`.

### 6.2 Repository release check

```bash
python scripts/check_repository.py --root . --log-level INFO
```

Purpose: check the public release package, including Python compilation, package metadata, repository layout, Markdown math rendering, claim boundary, artifact hashes, and the main certificate verification.

### 6.3 Certificate-chain verification

```bash
python scripts/replay_certificate_chain.py --root . --log-level INFO
```

Purpose: verify the four certificate-chain components without README, documentation, or repository-layout checks.

For component-level verification commands, see `docs/reproducibility.md`.

### 6.4 Developer regression tests

```bash
python -m unittest discover -s tests
```

These tests are not required for public certificate verification. They check that CLI entry points, Markdown math linting, narrative linting, and certificate-validation helpers have not regressed.

## 7. Expected success status

The main certificate verification should include:

```json
{
  "status": "passed",
  "certificate_verified": true,
  "threshold_proved": true,
  "certified_threshold": "0.83201",
  "failed_component_count": 0
}
```

The repository check should include:

```json
{
  "status": "passed",
  "failed_step_count": 0
}
```

For detailed output fields, see `docs/expected_outputs.md` and `docs/data_dictionary.md`.

## 8. Paper, citation, and license

The paper PDF is available at:

`paper/A_Certified_Lower_Bound_for_Lebesgues_Universal_Cover_Problem.pdf`

The LaTeX source is distributed through the paper release or arXiv source archive, not through this certificate-verification repository.

Please cite the repository using `CITATION.cff`. The code and public documentation are released under the MIT license; see `LICENSE`.

For troubleshooting, see `docs/reproducibility.md`. For common questions, see `docs/faq.md`.
