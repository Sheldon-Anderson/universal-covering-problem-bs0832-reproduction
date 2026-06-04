# A Reproducible Certificate for the Brass-Sharifi Lower Bound

This repository contains the public replay package for a certificate-based reproduction of the Brass-Sharifi lower bound in Lebesgue's universal cover problem.  The mathematical bound being reproduced is the published convex lower bound

```text
A(v) >= 0.832.
```

The Brass-Sharifi paper is the mathematical source of the bound.  This repository does not change the numerical value.  Its purpose is to make the computational part of the Brass-Sharifi argument replayable as a finite certificate: a recorded adaptive ledger, terminal-route replay data, local lower-bound certificates, integrity checks, and a final proof-obligation/signoff layer.

## 1. Lebesgue's universal covering problem

A planar set is a universal cover for sets of diameter one if every planar set of diameter one has a congruent copy inside it.  Equivalently, every such set can be moved by a rigid motion and placed inside the cover.  In the convex version considered here, the cover is required to be convex, and the goal is to minimize its area.

Brass and Sharifi proved the lower bound `0.832` for the convex problem.  They used three diameter-one test sets: a disk, an equilateral triangle, and a regular pentagon.  After a normalization, the disk is fixed, the triangle is translated, and the pentagon is rotated and translated.  The lower-bound computation studies the area of the convex hull of these three test sets over the normalized placement domain.

<p align="center">
  <img src="assets/figures/geometry.png" alt="Normalized placement of the three Brass-Sharifi test sets" width="45%">
</p>

## 2. What Brass-Sharifi proved

Brass and Sharifi reduced the convex lower-bound problem to a three-test-set placement problem.  Their proof combines geometric estimates with a computer search and establishes that the relevant convex hull area is always at least `0.832`.  This implies that every convex universal cover has area at least `0.832`.

The published paper describes the method and reports aggregate computation counts.  It was not published together with a modern replayable certificate containing terminal-route data, integrity audits, and a proof-obligation layer.

## 3. What this repository adds

This repository supplies that certificate layer.  It organizes the Brass-Sharifi computation as a finite record that can be checked by scripts:

1. an adaptive ledger recording the subdivision tree;
2. a terminal-route replay recording the terminal subdomains;
3. local certificate families that discharge each terminal route;
4. compact integrity records for large tables;
5. a proof-obligation layer connecting the replayed data to the lower-bound statement;
6. an author self-review signoff for the final certificate package.

The novelty of this repository is the certificate architecture, replay workflow, and audit structure.  It is not a new numerical lower bound.

## 4. Why the certificate supports the lower bound

The certificate checks the lower-bound computation through a finite chain.  The Branch-B domain record covers the reduced admissible placement domain by an enlarged replay domain.  The replay then covers that enlarged domain by finitely many terminal routes.  Each terminal route is assigned to a local certificate family, and each accepted local record proves the `0.832` lower bound on its route.  The proof-obligation layer records the finite assertions needed to aggregate these local checks into the certificate theorem.

The logic is:

```text
admissible domain
  -> Branch-B replay domain
  -> terminal routes
  -> local lower-bound certificates
  -> proof obligations
  -> BS0832 certificate statement
```

<p align="center">
  <img src="assets/figures/certificate_flow.png" alt="Certificate flow" width="35%">
</p>

## 5. Stage labels V106-V109

The labels `V106`-`V109` are public stage labels inherited from the development history of this reproduction package.  They are shorthand for versions `v0.10.6`-`v0.10.9`.  They are not mathematical constants and not theorem numbers.

<table>
  <thead>
    <tr>
      <th align="center" valign="middle">Stage</th>
      <th align="center" valign="middle">Development version</th>
      <th align="center" valign="middle">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center" valign="middle">V106</td>
      <td align="center" valign="middle">v0.10.6</td>
      <td align="center" valign="middle">Branch-B domain replay and kernel-closure checks</td>
    </tr>
    <tr>
      <td align="center" valign="middle">V107</td>
      <td align="center" valign="middle">v0.10.7</td>
      <td align="center" valign="middle">Independent replay and block-hash audit</td>
    </tr>
    <tr>
      <td align="center" valign="middle">V108</td>
      <td align="center" valign="middle">v0.10.8</td>
      <td align="center" valign="middle">Reproduction closure and proof-obligation binding</td>
    </tr>
    <tr>
      <td align="center" valign="middle">V109</td>
      <td align="center" valign="middle">v0.10.9</td>
      <td align="center" valign="middle">Final signoff adjudication and author self-review validation</td>
    </tr>
  </tbody>
</table>

## 6. Repository layout

```text
universal-cover-bs0832-reproduction/
├── README.md
├── README.zh-CN.md
├── ARTIFACTS.md
├── CERTIFICATE.md
├── EXPECTED_OUTPUTS.md
├── CITATION.cff
├── .github/workflows/
├── assets/figures/
├── app/domain/
├── scripts/
├── inputs/
├── certificate/
│   └── intermediate/
└── paper/
```

<table>
  <thead>
    <tr>
      <th align="center" valign="middle">Path</th>
      <th align="center" valign="middle">Role</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center" valign="middle"><code>assets/figures/</code></td>
      <td align="center" valign="middle">Figures used in the README files</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>app/domain/</code></td>
      <td align="center" valign="middle">Core Python logic for reading certificate files, checking integrity, validating signoff data, and running staged replay</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>scripts/</code></td>
      <td align="center" valign="middle">Command-line entry points; run them with <code>python -m scripts.&lt;name&gt;</code></td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>inputs/</code></td>
      <td align="center" valign="middle">Source certificate archives needed for staged reproduction</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>certificate/</code></td>
      <td align="center" valign="middle">Final certificate archive, author self-review file, manifest, and checksum list</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>certificate/intermediate/</code></td>
      <td align="center" valign="middle">Reference V106-V108 feedback archives used for comparison and reference-signed validation</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>paper/</code></td>
      <td align="center" valign="middle">Compiled PDF associated with this certificate repository</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>runs/</code></td>
      <td align="center" valign="middle">Generated output directory created by scripts; it is not tracked by Git</td>
    </tr>
  </tbody>
</table>

## 7. Required files

The staged reproduction expects these source archives under `inputs/`:

```text
feedback_v050_h004_local_proof_freeze_main.zip
feedback_v086_true_arb_and_local_tensor_port_v1.zip
feedback_v096_adaptive_full_ledger_rerun_executor.zip
adaptive_full_ledger_export_v096.zip
feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip
feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip
feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip
```

The final certificate files are under `certificate/`:

```text
feedback_v109_signed_author_self_review.zip
reviewer_signoff_v109.json
MANIFEST.json
SHA256SUMS.txt
```

Do not edit the ZIP archives by hand.  The verification scripts treat them as certificate data.

## 8. Installation

Python 3.10 or newer is recommended.

```bash
python -m pip install -r requirements.txt
```

A Conda environment file is also provided:

```bash
conda env create -f environment.yml
conda activate bs0832-reproduction
```

## 9. Quick final verification

Use this command when you only want to check the bundled final certificate and signoff:

```bash
python -m scripts.run_final_verification --root . --log-level INFO
```

Successful runs write:

```text
runs/final_verification/final_verification_summary.json
runs/final_verification/final_verification.log
```

The main success fields are:

```text
bs0832_final_repository_verification_passed = true
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

The value `theorem_ready=false` is expected.  This repository is an author-reviewed reproducible certificate package.  It is not a fully formalized proof in a proof assistant such as Lean, Coq, or Isabelle.

## 10. Full staged reproduction

Run the staged chain with:

```bash
python -m scripts.run_all_stages --root . --log-level INFO
```

This command runs V106, V107, V108, and two V109 modes.  It writes generated archives and summaries under `runs/`.

Expected top-level outputs include:

```text
runs/stage_v106/
runs/stage_v107/
runs/stage_v108/
runs/stage_v109_reference/
runs/stage_v109_generated/
runs/stage_all/stage_chain_summary.json
```

V107 performs the independent replay and block-hash audit.  It is usually the heaviest stage and may take noticeably longer than the other stages.

## 11. Individual stage commands

Run these commands if you want to inspect the stages one at a time.

### V106

```bash
python -m scripts.run_stage_v106 --root . --log-level INFO
```

Purpose: rebuild the Branch-B domain replay and kernel-closure feedback archive from the source inputs.

### V107

```bash
python -m scripts.run_stage_v107 --root . --log-level INFO
```

Purpose: perform the independent replay and compact block-hash audit.  To force V107 to use a freshly generated V106 archive:

```bash
python -m scripts.run_stage_v107 --root . \
  --v106-feedback-zip runs/stage_v106/feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip \
  --log-level INFO
```

### V108

```bash
python -m scripts.run_stage_v108 --root . --log-level INFO
```

Purpose: bind the replayed certificate data to proof obligations.  When using freshly generated V106 and V107 archives together, pass both paths:

```bash
python -m scripts.run_stage_v108 --root . \
  --v107-feedback-zip runs/stage_v107/feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip \
  --v106-feedback-zip runs/stage_v106/feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip \
  --log-level INFO
```

### V109: reference-signed mode

```bash
python -m scripts.run_stage_v109 --root . --mode reference-signed --log-level INFO
```

Purpose: validate the bundled author self-review signoff against the reference V108 archive.

### V109: generated-chain mode

```bash
python -m scripts.run_stage_v109 --root . --mode generated-chain \
  --v108-feedback-zip runs/stage_v108/feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip \
  --log-level INFO
```

Purpose: run V109 on a newly generated V108-style archive.  Unless a matching new signoff is supplied, this mode does not claim author self-review of the newly generated outer ZIP archive.

## 12. Reference-signed and generated-chain modes

The repository supports two V109 modes.

### Reference-signed mode

Reference-signed mode uses the reference V108 feedback archive included in this repository and checks that the author self-review file is bound to the SHA256 of that reference archive.

In other words, this mode verifies the certificate chain that is already included in the repository and has already been reviewed by the author. This is the mode used by the quick final verification.

### Generated-chain mode

Generated-chain mode uses a V108-style archive regenerated locally by the user.

A regenerated ZIP archive may have a different outer SHA256 even when its internal certificate content is logically equivalent to the reference archive. This can happen because ZIP files may record timestamps, compression settings, file ordering, or other metadata.

For this reason, the author self-review file included in this repository is not treated as a signature on an arbitrary newly generated ZIP archive. It is bound to the reference V108 archive whose SHA256 is recorded in the signoff file.

Thus, generated-chain mode checks that the newly generated certificate chain passes the expected structural and verification checks, but it does not automatically attach the repository's author self-review signoff to that new ZIP archive.

## 13. Why regenerated ZIP files may differ

A regenerated ZIP archive may differ from the bundled reference archive even when the relevant certificate content is equivalent. This is not automatically a reproduction failure.

**Why can the SHA256 differ?**  A ZIP archive can store metadata such as timestamps, compression settings, and file ordering. Those metadata may change when the archive is rebuilt.

**What does the repository check instead?**  The staged scripts check the internal certificate content: status files, schema checks, replay counts, boundary audits, selected content hashes, and signoff bindings where applicable.

**Why record both hashes?**  Stage summaries record both the generated ZIP hash and the reference ZIP hash for traceability. The outer ZIP hash is useful for identifying files, while the internal checks determine whether the certificate data pass the expected verification conditions.

## 14. Expected outputs

A successful final verification reports:

```text
status = success
bs0832_final_repository_verification_passed = true
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

A successful staged reproduction reports `status = success` in `runs/stage_all/stage_chain_summary.json`.  The generated-chain V109 run normally reports `theorem_ready_signed_candidate = false` unless a matching signoff for the regenerated V108 archive is supplied.

## 15. Troubleshooting

- If a required file is missing, check the `inputs/` and `certificate/` directories.
- If a SHA256 check fails, do not edit the ZIP archives manually.  Restore the original certificate files.
- If V107 takes a long time, this is expected; it performs the heaviest replay and hash-audit checks.
- If generated-chain V109 does not inherit the bundled signoff, this is expected.  The bundled signoff is tied to the reference V108 archive.

## 16. Citation and license

Please cite the Brass-Sharifi paper for the original lower-bound theorem.  If you use this repository, cite the accompanying paper and this repository once a public archive or DOI is available.

The code in this repository is released under the license in `LICENSE`.
