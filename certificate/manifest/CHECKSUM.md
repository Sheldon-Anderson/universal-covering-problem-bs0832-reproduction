# Checksum verification

The certificate-data hash gate covers the four archives in `certificate/final_chain/`.

The manifest file is:

```text
certificate/manifest/key_artifacts_sha256.txt
```

## Automatic check

The repository check verifies the listed hashes automatically:

```bash
python scripts/check_repository.py --root . --log-level INFO
```

The diagnostic CSV is written to:

```text
runs/repository_check/diagnostics/artifact_hashes.csv
```

## Manual check

On Linux or macOS, run:

```bash
sha256sum certificate/final_chain/*.zip
```

On Windows PowerShell, run:

```powershell
Get-FileHash certificate\final_chain\*.zip -Algorithm SHA256
```

Compare the computed digests with `certificate/manifest/key_artifacts_sha256.txt`. A mismatch means that a certificate archive has changed or the wrong archive is being checked.
