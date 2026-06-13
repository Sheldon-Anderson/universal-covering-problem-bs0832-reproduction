# Artifact and SHA256 policy

This repository separates certificate data, verification code, paper PDF, and documentation.

## Certificate data

The theorem-relevant certificate archives are stored in:

```text
certificate/final_chain/
```

The four archives are bundled with the repository:

```text
per_record_evidence_feedback.zip
construction_audit_feedback.zip
witness_construction_feedback.zip
final_adjudication_feedback.zip
```

No additional certificate data download is required for the public verification commands.

## Replay depth

The public replay code checks theorem-relevant records already bundled in the certificate archives. It verifies archive integrity, component status, individual evidence closure summaries, witness-domain orientation and shoelace certificates, and final claim-boundary checks.

It does not rerun the original geometric search and does not regenerate certificate records from scratch. The finite certificate theorem depends on the bundled certificate records and their deterministic replay checks.

## Hash policy

The SHA256 gate covers the four certificate-chain archives. The key manifest is:

```text
certificate/manifest/key_artifacts_sha256.txt
```

If any certificate-chain archive changes, the hash check in `scripts/check_repository.py` fails until the manifest is intentionally regenerated.

README files, docs, the paper PDF, and Python source files are checked by repository diagnostics and release control. They are not part of the certificate-data hash gate.

Manual checksum instructions are in `certificate/manifest/CHECKSUM.md`.

## Paper PDF

The repository includes the compiled paper PDF in `paper/`. The LaTeX source is distributed through the paper release or arXiv source archive, not through this certificate-verification repository.
