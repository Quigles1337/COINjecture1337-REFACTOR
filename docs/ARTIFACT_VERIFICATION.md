# Artifact Verification Guide

**Version:** 4.1.0
**Status:** Active
**Last Updated:** 2025-11-04

## Overview

COINjecture REFACTOR implements **institutional-grade artifact verification** using:
- **Sigstore** for keyless code signing (OIDC-based)
- **SLSA Provenance** (v0.2) for supply chain attestation
- **SHA256 checksums** for integrity verification
- **Dual SBOM formats** (CycloneDX + SPDX) for transparency

All release artifacts are:
1. Cryptographically signed with Sigstore cosign
2. Published with SLSA provenance attestations
3. Accompanied by SBOMs in both CycloneDX and SPDX formats
4. Traceable to specific CI runs and git commits

## Prerequisites

### Install Verification Tools

```bash
# Install cosign (Sigstore verification tool)
curl -sL https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o cosign
chmod +x cosign
sudo mv cosign /usr/local/bin/

# Verify cosign installation
cosign version
```

For other platforms:
- **macOS**: Use `cosign-darwin-amd64` or `cosign-darwin-arm64`
- **Windows**: Use `cosign-windows-amd64.exe`

## Verification Workflows

### 1. Verify Binary Signature

Binaries are signed using Sigstore's **keyless signing** with GitHub Actions OIDC.

```bash
# Download artifacts
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64.sig
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64.pem

# Verify signature
cosign verify-blob \
  --signature coinjectured-linux-amd64.sig \
  --certificate coinjectured-linux-amd64.pem \
  --certificate-identity-regexp='https://github.com/Quigles1337/COINjecture1337-REFACTOR/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  coinjectured-linux-amd64

# Expected output:
# Verified OK
```

**What this verifies:**
- ✅ Binary was signed by a GitHub Actions workflow
- ✅ Signature is tied to the specific repository
- ✅ Certificate was issued by GitHub OIDC provider
- ✅ Binary has not been tampered with

### 2. Verify Checksum

```bash
# Download checksum file
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64.sha256

# Verify checksum
shasum -a 256 -c coinjectured-linux-amd64.sha256

# Expected output:
# coinjectured-linux-amd64: OK
```

**What this verifies:**
- ✅ Binary integrity (detects any corruption or tampering)
- ✅ Matches the checksum computed during CI build

### 3. Verify SLSA Provenance Attestation

SLSA provenance provides **supply chain transparency** by documenting how the artifact was built.

```bash
# Download attestation
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64.att.json
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64.att.json.sig
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/coinjectured-linux-amd64.att.json.pem

# Verify attestation signature
cosign verify-blob \
  --signature coinjectured-linux-amd64.att.json.sig \
  --certificate coinjectured-linux-amd64.att.json.pem \
  --certificate-identity-regexp='https://github.com/Quigles1337/COINjecture1337-REFACTOR/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  coinjectured-linux-amd64.att.json

# Inspect attestation contents
cat coinjectured-linux-amd64.att.json | jq .
```

**Attestation Contents:**
```json
{
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "predicate": {
    "builder": {
      "id": "https://github.com/Quigles1337/COINjecture1337-REFACTOR/actions/runs/123456789"
    },
    "buildType": "https://github.com/Quigles1337/COINjecture1337-REFACTOR",
    "invocation": {
      "configSource": {
        "uri": "git+https://github.com/Quigles1337/COINjecture1337-REFACTOR@refs/heads/main",
        "digest": {
          "sha1": "abc123..."
        }
      }
    },
    "materials": [...]
  }
}
```

**What this verifies:**
- ✅ Built by official CI pipeline (not locally on dev machine)
- ✅ Traceable to specific git commit SHA
- ✅ Reproducible build metadata
- ✅ No unauthorized modifications to build process

### 4. Verify SBOM (Software Bill of Materials)

SBOMs provide a **complete inventory of dependencies**.

```bash
# Download SBOM (CycloneDX format)
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/sbom-rust-cyclonedx.json
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/sbom-rust-cyclonedx.json.sig
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/sbom-rust-cyclonedx.json.pem

# Verify SBOM signature
cosign verify-blob \
  --signature sbom-rust-cyclonedx.json.sig \
  --certificate sbom-rust-cyclonedx.json.pem \
  --certificate-identity-regexp='https://github.com/Quigles1337/COINjecture1337-REFACTOR/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  sbom-rust-cyclonedx.json

# Inspect SBOM
cat sbom-rust-cyclonedx.json | jq .
```

**SBOM Formats Available:**
- **CycloneDX JSON** - Modern, detailed format with licensing info
- **SPDX JSON** - ISO/IEC 5962:2021 standard format

**What this verifies:**
- ✅ Complete dependency tree
- ✅ Known vulnerabilities (via CVE lookups)
- ✅ License compliance
- ✅ Supply chain transparency

### 5. Verify Audit Reports

Security audit reports are also signed.

```bash
# Download audit report
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/audit-rust.json
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/audit-rust.json.sig
wget https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/v4.1.0/audit-rust.json.pem

# Verify audit signature
cosign verify-blob \
  --signature audit-rust.json.sig \
  --certificate audit-rust.json.pem \
  --certificate-identity-regexp='https://github.com/Quigles1337/COINjecture1337-REFACTOR/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  audit-rust.json

# Inspect audit results
cat audit-rust.json | jq .
```

## Automated Verification Script

For convenience, use our automated verification script:

```bash
#!/bin/bash
# verify-release.sh - Verify all artifacts for a release

VERSION="${1:-v4.1.0}"
PLATFORM="${2:-linux-amd64}"

BASE_URL="https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/download/${VERSION}"
BINARY="coinjectured-${PLATFORM}"

echo "Verifying COINjecture ${VERSION} for ${PLATFORM}..."

# 1. Download all artifacts
wget -q "${BASE_URL}/${BINARY}"
wget -q "${BASE_URL}/${BINARY}.sig"
wget -q "${BASE_URL}/${BINARY}.pem"
wget -q "${BASE_URL}/${BINARY}.sha256"
wget -q "${BASE_URL}/${BINARY}.att.json"
wget -q "${BASE_URL}/${BINARY}.att.json.sig"
wget -q "${BASE_URL}/${BINARY}.att.json.pem"

# 2. Verify checksum
echo "[1/3] Verifying checksum..."
if shasum -a 256 -c "${BINARY}.sha256" 2>/dev/null; then
    echo "✅ Checksum verified"
else
    echo "❌ Checksum verification FAILED"
    exit 1
fi

# 3. Verify binary signature
echo "[2/3] Verifying binary signature..."
if cosign verify-blob \
    --signature "${BINARY}.sig" \
    --certificate "${BINARY}.pem" \
    --certificate-identity-regexp='https://github.com/Quigles1337/COINjecture1337-REFACTOR/.*' \
    --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
    "${BINARY}" >/dev/null 2>&1; then
    echo "✅ Binary signature verified"
else
    echo "❌ Binary signature verification FAILED"
    exit 1
fi

# 4. Verify attestation
echo "[3/3] Verifying SLSA attestation..."
if cosign verify-blob \
    --signature "${BINARY}.att.json.sig" \
    --certificate "${BINARY}.att.json.pem" \
    --certificate-identity-regexp='https://github.com/Quigles1337/COINjecture1337-REFACTOR/.*' \
    --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
    "${BINARY}.att.json" >/dev/null 2>&1; then
    echo "✅ Attestation verified"
else
    echo "❌ Attestation verification FAILED"
    exit 1
fi

echo ""
echo "🎉 All verifications passed!"
echo "✅ Binary integrity: VERIFIED"
echo "✅ Signature: VERIFIED"
echo "✅ Provenance: VERIFIED"
echo ""
echo "Safe to use: ${BINARY}"
```

**Usage:**
```bash
chmod +x verify-release.sh
./verify-release.sh v4.1.0 linux-amd64
```

## Security Best Practices

### For Users

1. **Always verify signatures** before running binaries
2. **Check attestations** to ensure CI-built artifacts
3. **Review SBOMs** for unexpected dependencies
4. **Verify checksums** match published values
5. **Use official releases** from GitHub Releases only

### For Developers

1. **Never skip verification** when testing releases
2. **Report suspicious artifacts** to security@example.com
3. **Keep cosign updated** to latest version
4. **Audit dependencies** regularly via SBOMs
5. **Monitor security reports** from CI pipeline

## Incident Response

If verification fails:

1. **STOP** - Do not use the artifact
2. **Report** - File an issue with details:
   - Artifact name and version
   - Verification step that failed
   - Error messages
   - Platform and cosign version
3. **Wait** - Do not proceed until investigation complete
4. **Communicate** - Notify team via security channel

## Supported Platforms

| Platform | Binary | Status |
|----------|--------|--------|
| Linux x86_64 | `coinjectured-linux-amd64` | ✅ Fully supported |
| macOS x86_64 | `coinjectured-macos-amd64` | ✅ Fully supported |
| macOS ARM64 | `coinjectured-macos-arm64` | ✅ Fully supported |
| Windows x86_64 | `coinjectured-windows-amd64.exe` | ✅ Fully supported |

## Technical Details

### Sigstore Keyless Signing

COINjecture uses **Sigstore keyless signing**, which:
- Eliminates need for managing private keys
- Uses GitHub OIDC tokens for identity
- Certificates are short-lived (10 minutes)
- All signatures recorded in **Rekor** transparency log

**Rekor Verification:**
```bash
# Look up signature in transparency log
REKOR_UUID=$(cosign verify-blob ... | jq -r .rekorUUID)
rekor-cli get --uuid "$REKOR_UUID"
```

### SLSA Provenance

We implement **SLSA Build Level 2**:
- ✅ Source integrity (git commit hash)
- ✅ Build service (GitHub Actions)
- ✅ Build as code (workflows in repo)
- ✅ Ephemeral environment (fresh runners)
- ✅ Parameterless builds
- ⚠️ Non-falsifiable (working toward Level 3)

## References

- [Sigstore Documentation](https://docs.sigstore.dev/)
- [SLSA Framework](https://slsa.dev/)
- [CycloneDX SBOM Specification](https://cyclonedx.org/)
- [SPDX Specification](https://spdx.dev/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

## Emergency Contacts

- **Security Team**: security@example.com
- **Incident Commander**: @Quigles1337
- **On-Call SRE**: sre-oncall@example.com

---

**Remember:** Verification is not optional. It's the final line of defense against supply chain attacks.
