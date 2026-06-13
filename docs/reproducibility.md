# Reproducibility guide

The repository already includes the certificate data in `certificate/final_chain/`. The public scripts replay theorem-relevant checks from these bundled records. They do not rerun the original geometric search and do not regenerate the certificate records from scratch.

## Validation environment

The public replay scripts use the Python standard library. Python 3.10 or later is supported; Python 3.11 is recommended for release verification.

Generated files under `runs/` are local outputs and should not be committed.

## Standard run

The public `python scripts/...` commands can be run directly from an unpacked source tree; no editable installation is required.

```bash
python scripts/verify_certificate.py --root . --log-level INFO
python scripts/check_repository.py --root . --log-level INFO
```

## Windows PowerShell

```powershell
python scripts\verify_certificate.py --root . --log-level INFO
python scripts\check_repository.py --root . --log-level INFO
```

## Optional editable installation

Editable installation is useful if you want the `ucbs-*` console commands, but it is not required for the public `python scripts/...` commands.

```bash
python -m pip install --upgrade pip setuptools
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps --no-build-isolation
ucbs-verify-certificate --root . --log-level INFO
ucbs-check-repository --root . --log-level INFO
```

## Explicit certificate archives

```bash
python scripts/verify_certificate.py \
  --root . \
  --per-record-evidence-zip certificate/final_chain/per_record_evidence_feedback.zip \
  --construction-audit-zip certificate/final_chain/construction_audit_feedback.zip \
  --witness-construction-zip certificate/final_chain/witness_construction_feedback.zip \
  --final-adjudication-zip certificate/final_chain/final_adjudication_feedback.zip \
  --log-level INFO
```

## Certificate-chain verification

```bash
python scripts/replay_certificate_chain.py --root . --log-level INFO
```

This command verifies the four certificate-chain components without README, documentation, or repository-layout checks.

## Component-level verification commands

These commands isolate one component. They are useful when a user wants to inspect the source of a certificate-chain failure.

```bash
python scripts/replay_per_record_evidence.py --root . --log-level INFO
python scripts/replay_construction_audit.py --root . --log-level INFO
python scripts/replay_witness_construction.py --root . --log-level INFO
python scripts/replay_final_adjudication.py --root . --log-level INFO
```

| Command | Purpose |
|---|---|
| `replay_per_record_evidence.py` | Verifies individual evidence closure for supporting local records. |
| `replay_construction_audit.py` | Verifies construction, rounding, and support-to-area records. |
| `replay_witness_construction.py` | Verifies witness domains, orientation estimates, and shoelace lower bounds. |
| `replay_final_adjudication.py` | Verifies final proof obligations and claim-boundary records. |

## Developer regression tests

The public certificate verification does not require running the test suite. The tests protect CLI entry points, Markdown math linting, narrative linting, and certificate-validation helpers against future regressions.

```bash
python -m unittest discover -s tests
```


## Editing public Markdown math

This policy applies to GitHub Markdown files such as `README.md`, `README.zh-CN.md`, and `docs/*.md`. It does not apply to the LaTeX paper.

- Use `$...$` for short inline formulas.
- Use fenced `math` blocks for display formulas in public Markdown.
- Do not use `\(...\)`, `\[...\]`, or `$$...$$` in public Markdown.
- Avoid `\operatorname` in GitHub Markdown; use `\mathrm{area}` and `\mathrm{conv}` instead.
- Write `\mathcal{U}` with braces rather than `\mathcal U`.

## Useful options

- `--root`: repository root.
- `--run-id`: output directory name under `runs/`.
- `--log-level`: one of `DEBUG`, `INFO`, `WARNING`, or `ERROR`.
- `--artifact-root`: directory containing the four certificate-chain archives.

## Troubleshooting

- If certificate verification fails, inspect `runs/certificate_verification/log/certificate_verification.log` and `runs/certificate_verification/diagnostics/failed_component_checks.csv`.
- If repository check fails, inspect `runs/repository_check/diagnostics/failed_checks.csv`.
- If README math lint fails, use `$...$` for simple inline math and fenced `math` blocks for display math.
- If an artifact hash check fails, do not edit the four files in `certificate/final_chain/` manually. Regenerate the certificate data and manifest intentionally.
- Do not create release artifacts by manually compressing a local working tree that contains `.git/`. Use a GitHub release archive or another clean packaging workflow.
