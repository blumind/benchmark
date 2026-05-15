# BluMind — Public PGP Keys

This directory contains the public PGP key used to encrypt confidential
material sent to the BluMind Benchmark, including credentials submitted
by participating labs.

The private key is held exclusively by BluMind and is never published.

## Active key

| Field         | Value                                          |
| ------------- | ---------------------------------------------- |
| File          | `blumind-submissions.asc`                      |
| User ID       | `BluMind Submissions <submissions@blumind.es>` |
| Algorithm     | EdDSA / ECDH (Curve25519)                      |
| Created       | 2026-05-15                                     |
| Expires       | Never                                          |
| Fingerprint   | `42E1 6A9D FD54 0917 4B3B  AA2A F329 316C 1392 A8F2` |

## How to import the key

From the root of this repository:

```bash
gpg --import system/keys/blumind-submissions.asc
```

## How to verify the fingerprint

After importing, run:

```bash
gpg --fingerprint submissions@blumind.es
```

The output must match the fingerprint shown above **exactly**. If it does
not match, do not use the key — contact BluMind through the official
channels listed in
[`../../docs/submission_guide.md`](../../docs/submission_guide.md) to
report a possible compromise.

## How to encrypt a file for BluMind

Once the key is imported and the fingerprint has been verified:

```bash
gpg --encrypt --armor --recipient submissions@blumind.es \
    --output credentials.asc credentials.txt
```

The resulting `credentials.asc` is safe to send by email to
`submissions@blumind.es`. Only the holder of the BluMind private key can
decrypt it.

## Key rotation and revocation

If the active key is ever rotated or revoked, the change is announced
through BluMind's official communications and reflected in this file,
including the fingerprint of the new active key. Historical keys are
preserved here for traceability and clearly marked as superseded.
