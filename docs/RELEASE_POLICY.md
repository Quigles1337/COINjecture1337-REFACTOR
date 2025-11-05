# Release Policy & Signing Procedures

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** COINjecture Release Engineering
**Status:** ACTIVE

---

## Table of Contents

1. [Overview](#overview)
2. [Versioning Strategy](#versioning-strategy)
3. [Release Types](#release-types)
4. [Release Process](#release-process)
5. [Artifact Signing](#artifact-signing)
6. [SBOM Generation](#sbom-generation)
7. [Security Scanning](#security-scanning)
8. [Distribution](#distribution)
9. [Rollback Procedures](#rollback-procedures)
10. [Post-Release Validation](#post-release-validation)

---

## Overview

This document defines the **institutional-grade release policy** for COINjecture, ensuring:

✅ **Reproducible Builds** - Deterministic artifacts across platforms
✅ **Supply Chain Security** - Signed artifacts with SBOM attestation
✅ **Change Control** - Traceable releases with approval gates
✅ **Zero-Downtime Deploys** - Gradual rollout with automatic rollback
✅ **Compliance** - Audit trail for financial institution requirements

---

## Versioning Strategy

### Semantic Versioning (SemVer 2.0)

**Format:** `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

**Examples:**
- `v4.0.0` - Major release (breaking changes)
- `v4.1.0` - Minor release (new features, backwards compatible)
- `v4.1.1` - Patch release (bug fixes)
- `v4.2.0-rc.1` - Release candidate
- `v4.2.0-alpha.3` - Alpha pre-release
- `v4.2.0+20251104.abc123` - Build metadata

### Version Incrementing Rules

**MAJOR (X.0.0):**
- Breaking API changes
- Consensus protocol changes requiring hard fork
- Removal of deprecated features
- Golden vector incompatibility

**MINOR (x.Y.0):**
- New features (backwards compatible)
- Performance improvements
- New API endpoints
- Security enhancements (non-breaking)

**PATCH (x.x.Z):**
- Bug fixes
- Security patches (backwards compatible)
- Documentation updates
- Dependency updates (non-breaking)

**PRERELEASE (-alpha, -beta, -rc):**
- `-alpha.N` - Feature development, unstable
- `-beta.N` - Feature complete, testing phase
- `-rc.N` - Release candidate, production-ready testing

### Version Compatibility Matrix

| Component | Current Version | Min Compatible | Max Compatible |
|-----------|----------------|----------------|----------------|
| **Rust Core** | v4.0.0 | v4.0.0 | v4.x.x |
| **Go Daemon** | v4.0.0 | v3.17.0 | v4.x.x |
| **Python Shims** | v4.0.0 | v3.0.0 | v4.x.x |
| **Golden Vectors** | v4.0.0 | v4.0.0 | v4.0.x |

**Rules:**
- Rust core version MUST match golden vectors exactly
- Go daemon can lag by 1 minor version (e.g., v4.1.0 works with v4.0.0 core)
- Python shims maintain backwards compatibility for 2 major versions

---

## Release Types

### 1. Stable Release

**Cadence:** Monthly (first Tuesday of month)
**Branch:** `main`
**Testing:** Full CI/CD + 7-day soak test
**Approval:** Release Manager + CTO
**Example:** `v4.1.0`

**Criteria:**
- ✅ All CI/CD tests passing
- ✅ Parity validation 100% match rate
- ✅ Determinism tests pass across all platforms
- ✅ Zero critical/high vulnerabilities
- ✅ SLO budget remaining ≥ 50%
- ✅ Release notes complete
- ✅ SBOM generated and signed

**Soak Test Protocol:**
```
Day 1-2: Canary deployment (10% traffic)
Day 3-4: Expanded deployment (25% traffic)
Day 5-6: Majority deployment (75% traffic)
Day 7: Full deployment (100% traffic)
```

---

### 2. Hotfix Release

**Cadence:** As needed (emergency)
**Branch:** `hotfix/vX.Y.Z`
**Testing:** Reduced CI/CD (critical path only)
**Approval:** On-call engineer + Platform Lead
**Example:** `v4.1.1`

**Criteria:**
- ✅ Fixes P0/P1 incident
- ✅ Minimal scope (single issue)
- ✅ Parity validation passes
- ✅ No new features
- ✅ Emergency PIR required

**Fast-Track Timeline:**
```
Hour 0: Incident declared
Hour 1: Hotfix branch created, fix implemented
Hour 2: Tests passing, PR approved
Hour 3: Release built and signed
Hour 4: Canary deployment (10%)
Hour 6: Full deployment (100%)
Hour 12: Post-deployment PIR
```

---

### 3. Pre-Release (Alpha/Beta/RC)

**Cadence:** Weekly (during development)
**Branch:** `develop`
**Testing:** Full CI/CD (no soak test)
**Approval:** Release Manager
**Example:** `v4.2.0-rc.1`

**Criteria:**
- ✅ All CI/CD tests passing
- ✅ Feature flag protected
- ✅ Not deployed to production
- ✅ Opt-in only for testers

**Alpha → Beta → RC Progression:**
```
Alpha: Feature development, unstable API
  ↓ (2 weeks, 50+ test executions)
Beta: Feature complete, API frozen
  ↓ (2 weeks, 500+ test executions)
RC: Production-ready candidate
  ↓ (1 week, 5000+ test executions)
Stable: Released to production
```

---

### 4. Long-Term Support (LTS)

**Cadence:** Annually (April release)
**Branch:** `lts/vX`
**Testing:** Full CI/CD + 30-day soak test
**Approval:** Executive sponsor + CTO
**Example:** `v4.0.0-lts`

**Support Timeline:**
- **Active Support:** 18 months (bug fixes + security patches)
- **Security Support:** 36 months (security patches only)
- **End of Life:** 48 months (no support)

**Current LTS Versions:**
- `v4.0.0-lts` - Active until 2026-10-01
- `v3.0.0-lts` - Security until 2025-04-01
- `v2.0.0-lts` - EOL (no support)

---

## Release Process

### Phase 1: Planning (T-14 days)

**1.1. Create Release Issue**

```markdown
## Release: v4.1.0

**Target Date:** 2025-11-18
**Release Manager:** @alice
**Type:** Stable

### Checklist
- [ ] CHANGELOG.md updated
- [ ] Version bumped in all components
- [ ] Golden vectors validated
- [ ] Dependency updates reviewed
- [ ] Security scan clean
- [ ] Release notes drafted
- [ ] Rollback plan documented
```

**1.2. Version Bump**

```bash
# Update version in all components
./scripts/bump-version.sh 4.1.0

# Files updated:
# - rust/coinjecture-core/Cargo.toml
# - go/cmd/coinjectured/version.go
# - python/pyproject.toml
# - package.json
# - CHANGELOG.md
```

**1.3. Freeze `develop` Branch**

```bash
# Merge all approved PRs
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/v4.1.0
git push -u origin release/v4.1.0
```

---

### Phase 2: Testing (T-7 days)

**2.1. Run Full CI/CD**

```bash
# Trigger all workflows
gh workflow run ci.yml --ref release/v4.1.0
gh workflow run determinism.yml --ref release/v4.1.0
gh workflow run parity.yml --ref release/v4.1.0
gh workflow run security.yml --ref release/v4.1.0
```

**Wait for all quality gates to pass** (14 jobs):
```
✅ Lint (Rust, Python, Go)
✅ Tests (Unit, Integration, E2E)
✅ Golden Vectors
✅ Determinism (Linux, macOS, Windows)
✅ Parity Validation (1K blocks, 100% match)
✅ Security Scans (cargo audit, pip-audit, govulncheck)
✅ Coverage Gate (≥70% new, ≥50% overall)
```

**2.2. Property-Based Testing**

```bash
# Run 10,000 examples per property
cd rust/coinjecture-core
cargo test --release --test property_tests -- --nocapture

cd python/tests/property
pytest test_codec_properties.py -v --hypothesis-seed=random
```

**2.3. Fuzz Testing**

```bash
# Run fuzzer for 6 hours (corpus from previous runs)
cd rust/coinjecture-core
cargo fuzz run fuzz_decode_block -- -max_total_time=21600
cargo fuzz run fuzz_subset_sum_verify -- -max_total_time=21600
```

**Expected Results:**
- Zero crashes
- Zero hangs (all complete within budget)
- Coverage increase ≥ 5% over previous run

---

### Phase 3: Approval (T-3 days)

**3.1. Release Notes Review**

**Template:**
```markdown
# COINjecture v4.1.0 Release Notes

**Release Date:** 2025-11-18
**Release Manager:** Alice Johnson
**Type:** Stable

## 🎯 Highlights

- **Performance:** 30% faster block validation on Server tier
- **Security:** Epoch replay cache now persisted to disk
- **Observability:** 3 new Grafana dashboards for SLO tracking

## ✨ New Features

- **[CORE-123]** Persistent epoch replay cache (#456)
- **[NET-456]** IPFS pin quorum with signed manifests (#789)
- **[OBS-789]** Real-time parity validation dashboard (#234)

## 🐛 Bug Fixes

- **[BUG-111]** Fix race condition in P2P peer discovery (#567)
- **[BUG-222]** Correct merkle root computation for empty tx list (#890)

## 🔒 Security

- **[SEC-002]** Enhanced epoch replay protection with HMAC binding
- **[SEC-005]** IPFS pinning quorum prevents missing CIDs

## 📊 Performance

| Metric | v4.0.0 | v4.1.0 | Change |
|--------|--------|--------|--------|
| Header Hash (p99) | 0.8ms | 0.6ms | -25% |
| Block Validation (Desktop, p95) | 280s | 195s | -30% |
| Memory Usage (Server) | 14GB | 12GB | -14% |

## 🔄 Breaking Changes

None. Fully backwards compatible with v4.0.x.

## 📦 Artifact Hashes

**Rust Core:**
```
libcoinjecture_core-v4.1.0-x86_64-linux.so
SHA256: a1b2c3d4e5f6...
```

**Go Daemon:**
```
coinjectured-v4.1.0-x86_64-linux
SHA256: f6e5d4c3b2a1...
```

## 🔗 Links

- **GitHub Release:** https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases/tag/v4.1.0
- **Documentation:** https://docs.coinjecture.io/v4.1.0
- **Migration Guide:** https://docs.coinjecture.io/v4.1.0/migration
- **SBOM (CycloneDX):** https://github.com/.../releases/download/v4.1.0/sbom.json
```

**3.2. Approval Gates**

**Required Approvals:**
1. **Release Manager** - Process compliance
2. **Platform Lead** - Technical review
3. **Security Team** - Vulnerability sign-off
4. **CTO** - Final authorization (for stable releases)

**GitHub PR Labels:**
- `release/approved` - All approvals obtained
- `release/signed` - Artifacts signed and verified
- `release/sbom` - SBOM generated and attached

---

### Phase 4: Build & Sign (T-1 day)

**4.1. Create Git Tag**

```bash
# On release branch, create signed tag
git tag -s v4.1.0 -m "Release v4.1.0: Performance improvements & security enhancements"

# Verify tag signature
git tag -v v4.1.0

# Push tag (triggers release workflow)
git push origin v4.1.0
```

**4.2. Build Artifacts**

**Triggered by tag push via GitHub Actions:**

```yaml
# .github/workflows/release.yml
on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-rust:
    runs-on: ubuntu-latest
    steps:
      - name: Build release binary
        run: |
          cd rust/coinjecture-core
          cargo build --release --locked

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: libcoinjecture_core-${{ github.ref_name }}-x86_64-linux
          path: target/release/libcoinjecture_core.so
```

**Build Matrix:**
| Component | Platform | Arch | Output |
|-----------|----------|------|--------|
| Rust Core | Linux | x86_64 | `libcoinjecture_core.so` |
| Rust Core | macOS | arm64 | `libcoinjecture_core.dylib` |
| Rust Core | Windows | x86_64 | `coinjecture_core.dll` |
| Go Daemon | Linux | x86_64 | `coinjectured` |
| Go Daemon | Linux | arm64 | `coinjectured-arm64` |
| Python Wheel | Any | Any | `coinjecture-4.1.0-py3-none-any.whl` |

**4.3. Generate Checksums**

```bash
# SHA256 checksums for all artifacts
cd dist/
sha256sum * > checksums-v4.1.0.txt

# Sign checksums file
gpg --detach-sign --armor checksums-v4.1.0.txt
```

**4.4. Sign Artifacts (Sigstore)**

```bash
# Install cosign
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# Sign using keyless (OIDC with GitHub)
cosign sign-blob \
  --bundle libcoinjecture_core.so.bundle \
  libcoinjecture_core.so

# Verify signature
cosign verify-blob \
  --bundle libcoinjecture_core.so.bundle \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  libcoinjecture_core.so
```

**Signature Artifacts:**
- `*.bundle` - Sigstore bundle (signature + cert + transparency log entry)
- `*.sig` - Detached signature
- `checksums-v4.1.0.txt.asc` - GPG-signed checksums

---

### Phase 5: SBOM Generation

**5.1. Generate SBOM (CycloneDX)**

```bash
# Rust dependencies
cargo install cargo-cyclonedx
cd rust/coinjecture-core
cargo cyclonedx --format json --output-pattern sbom-rust-{version}

# Go dependencies
go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
cd go
cyclonedx-gomod app -json -output sbom-go-v4.1.0.json

# Python dependencies
pip install cyclonedx-bom
cd python
cyclonedx-py --format json --output sbom-python-v4.1.0.json

# Merge all SBOMs
./scripts/merge-sboms.sh \
  sbom-rust-v4.1.0.json \
  sbom-go-v4.1.0.json \
  sbom-python-v4.1.0.json \
  --output sbom-v4.1.0.json
```

**5.2. Sign SBOM**

```bash
# Sign SBOM with cosign
cosign attest-blob \
  --predicate sbom-v4.1.0.json \
  --type cyclonedx \
  --bundle sbom-v4.1.0.json.bundle
```

**5.3. Upload to Transparency Log**

```bash
# Verify SBOM in Rekor transparency log
rekor-cli search --artifact sbom-v4.1.0.json

# Output:
# Found matching entries (1):
# UUID: 5e9a7b...
# Index: 1234567
# Integrated: 2025-11-18T10:00:00Z
```

**SBOM Format (CycloneDX 1.5):**
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "serialNumber": "urn:uuid:a1b2c3d4-...",
  "version": 1,
  "metadata": {
    "timestamp": "2025-11-18T10:00:00Z",
    "component": {
      "type": "application",
      "name": "coinjecture",
      "version": "4.1.0"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "serde",
      "version": "1.0.193",
      "purl": "pkg:cargo/serde@1.0.193",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "..."
        }
      ]
    }
  ],
  "dependencies": [...]
}
```

---

### Phase 6: Security Scanning

**6.1. Vulnerability Scan**

```bash
# Rust
cargo audit --json > audit-rust-v4.1.0.json

# Python
pip-audit --format json > audit-python-v4.1.0.json

# Go
govulncheck -json ./... > audit-go-v4.1.0.json
```

**Acceptance Criteria:**
- **CRITICAL (CVSS ≥9.0):** 0 vulnerabilities
- **HIGH (CVSS ≥7.0):** ≤ 2 vulnerabilities (with mitigation plan)
- **MEDIUM (CVSS ≥4.0):** ≤ 10 vulnerabilities

**6.2. License Compliance**

```bash
# Check for incompatible licenses
cargo install cargo-license
cargo license --json > licenses-v4.1.0.json

# Verify all licenses are approved
./scripts/check-licenses.sh licenses-v4.1.0.json
```

**Approved Licenses:**
- MIT, Apache-2.0, BSD-3-Clause (permissive)
- MPL-2.0 (copyleft - allowed for dependencies)

**Forbidden Licenses:**
- GPL-3.0, AGPL-3.0 (strong copyleft)
- Proprietary licenses

---

### Phase 7: Deployment (Release Day)

**7.1. Merge to `main`**

```bash
# Final merge
git checkout main
git merge --no-ff release/v4.1.0 -m "Release v4.1.0"
git push origin main

# Tag main branch
git tag -s v4.1.0 -m "Release v4.1.0"
git push origin v4.1.0
```

**7.2. Create GitHub Release**

```bash
# Using GitHub CLI
gh release create v4.1.0 \
  --title "COINjecture v4.1.0: Performance & Security Improvements" \
  --notes-file docs/release-notes/v4.1.0.md \
  --draft=false \
  --prerelease=false \
  dist/*
```

**Attached Assets:**
```
✅ libcoinjecture_core-v4.1.0-x86_64-linux.so
✅ libcoinjecture_core-v4.1.0-x86_64-linux.so.bundle
✅ coinjectured-v4.1.0-x86_64-linux
✅ coinjectured-v4.1.0-x86_64-linux.bundle
✅ coinjecture-4.1.0-py3-none-any.whl
✅ checksums-v4.1.0.txt
✅ checksums-v4.1.0.txt.asc
✅ sbom-v4.1.0.json
✅ sbom-v4.1.0.json.bundle
```

**7.3. Gradual Rollout**

**See [RUNBOOKS.md](RUNBOOKS.md#gradual-rollout-procedure) for detailed steps.**

**Timeline:**
```
T+0h: Canary (10% traffic) - us-west-1a
T+6h: Expand to 25% - us-west-1a,b
T+12h: Expand to 50% - us-west-1,2
T+24h: Expand to 75% - us-west-1,2,3
T+48h: Full rollout (100%) - all regions
```

**Automatic Rollback Triggers:**
- Parity mismatch detected
- SLO breach (API availability < 99.9%)
- Error rate spike (> 2x baseline)
- Manual rollback command

---

## Artifact Signing

### Signing Methods

**1. Sigstore (Keyless, Recommended)**

**Advantages:**
- No key management (uses OIDC)
- Transparency log integration (Rekor)
- Short-lived certificates
- GitHub Actions native support

**Process:**
```bash
# Sign artifact
cosign sign-blob \
  --output-signature artifact.sig \
  --output-certificate artifact.crt \
  artifact.bin

# Verify
cosign verify-blob \
  --certificate artifact.crt \
  --signature artifact.sig \
  --certificate-identity-regexp ".*@coinjecture\\.io" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  artifact.bin
```

---

**2. GPG (Traditional)**

**Use Cases:**
- Offline signing
- Long-term archival
- Air-gapped environments

**Process:**
```bash
# Generate key (if needed)
gpg --full-generate-key
# Select: (1) RSA and RSA, 4096 bits, no expiration
# Identity: COINjecture Release Engineering <releases@coinjecture.io>

# Sign artifact
gpg --detach-sign --armor artifact.bin

# Verify
gpg --verify artifact.bin.asc artifact.bin
```

**Key Management:**
- **Master Key:** Offline, air-gapped storage
- **Subkey:** GitHub Actions Secrets, rotated quarterly
- **Backup:** Encrypted USB drives (3 copies, geographically distributed)

---

### Signature Verification Guide

**For Users:**

```bash
# 1. Download release
wget https://github.com/.../releases/download/v4.1.0/libcoinjecture_core.so
wget https://github.com/.../releases/download/v4.1.0/libcoinjecture_core.so.bundle

# 2. Verify signature
cosign verify-blob \
  --bundle libcoinjecture_core.so.bundle \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  libcoinjecture_core.so

# Expected output:
# Verified OK

# 3. Check transparency log
rekor-cli get --uuid $(cat libcoinjecture_core.so.bundle | jq -r .rekorBundle.payload.logID)
```

---

## SBOM Generation

### Format Standards

**Primary:** CycloneDX 1.5 (JSON)
**Secondary:** SPDX 2.3 (for compliance)

**Why CycloneDX?**
- Better dependency graph representation
- Vulnerability enrichment (VEX integration)
- License compliance tracking
- Widely adopted in security tools

### SBOM Content Requirements

**Minimum Required Fields:**
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "components": [
    {
      "type": "library",
      "name": "<package-name>",
      "version": "<version>",
      "purl": "<package-url>",
      "hashes": [{"alg": "SHA-256", "content": "..."}],
      "licenses": [{"license": {"id": "MIT"}}],
      "externalReferences": [
        {"type": "vcs", "url": "https://github.com/..."}
      ]
    }
  ],
  "vulnerabilities": [...],  // VEX data
  "dependencies": [...]
}
```

### SBOM Distribution

**Public Releases:**
- Attached to GitHub release
- Published to SBOM repository: `ghcr.io/quigles1337/coinjecture/sbom`
- Indexed in transparency log (Rekor)

**Private Builds:**
- Stored in artifact repository with access control
- Available via API: `GET /api/v1/sbom/{version}`

---

## Security Scanning

### Pre-Release Scans

**1. Dependency Vulnerabilities**
```bash
# Fail release if critical vulns found
cargo audit --deny warnings
pip-audit --require-hashes --strict
govulncheck -test ./...
```

**2. Static Analysis**
```bash
# Rust
cargo clippy --all-targets --all-features -- -D warnings

# Go
golangci-lint run --enable-all

# Python
bandit -r src/ -ll
```

**3. Container Scanning**
```bash
# If using Docker
trivy image ghcr.io/quigles1337/coinjecture:v4.1.0 --severity CRITICAL,HIGH
```

### Post-Release Monitoring

**Continuous Scanning:**
- GitHub Dependabot alerts
- Daily `cargo audit` / `pip-audit` / `govulncheck` runs
- CVE monitoring via NVD API

**Patch SLA:**
| Severity | Patch Within | Deploy Within |
|----------|-------------|---------------|
| Critical (≥9.0) | 24 hours | 48 hours |
| High (≥7.0) | 7 days | 14 days |
| Medium (≥4.0) | 30 days | 60 days |
| Low (<4.0) | Next release | Next release |

---

## Distribution

### Distribution Channels

**1. GitHub Releases (Primary)**
- URL: `https://github.com/Quigles1337/COINjecture1337-REFACTOR/releases`
- Artifacts: Binaries, checksums, signatures, SBOMs
- Auto-generated from tags

**2. Container Registry**
- Registry: `ghcr.io/quigles1337/coinjecture`
- Tags: `v4.1.0`, `v4.1`, `v4`, `latest`
- Signed with cosign

**3. Package Managers**
- **Python:** PyPI (`pip install coinjecture`)
- **Rust:** crates.io (`cargo add coinjecture-core`)
- **Go:** Go modules (`go get github.com/Quigles1337/COINjecture1337-REFACTOR/go`)

**4. Binary Archives**
- URL: `https://releases.coinjecture.io/v4.1.0/`
- CDN: CloudFlare (cached globally)
- Retention: Indefinite for stable, 90 days for pre-releases

### Download Verification

**Users MUST verify downloads:**

```bash
# 1. Download artifact + checksum + signature
wget https://github.com/.../releases/download/v4.1.0/coinjectured
wget https://github.com/.../releases/download/v4.1.0/checksums-v4.1.0.txt
wget https://github.com/.../releases/download/v4.1.0/checksums-v4.1.0.txt.asc

# 2. Verify checksum signature
gpg --verify checksums-v4.1.0.txt.asc checksums-v4.1.0.txt

# 3. Verify artifact checksum
sha256sum -c checksums-v4.1.0.txt --ignore-missing

# Expected output:
# coinjectured: OK
```

---

## Rollback Procedures

### Rollback Triggers

**Automatic:**
- Parity mismatch detected (SLO-007 violation)
- API availability < 99.9% for 5 minutes
- Error rate > 2x baseline for 10 minutes
- Memory leak detected (OOM crashes)

**Manual:**
- On-call engineer determination
- Customer-reported regressions
- Security vulnerability discovery

### Rollback Process

**See [RUNBOOKS.md](RUNBOOKS.md#emergency-rollback) for detailed steps.**

**Quick Reference:**
```bash
# 1. Trigger rollback
kubectl rollout undo deployment/coinjecture-node

# 2. Verify rollback
kubectl rollout status deployment/coinjecture-node

# 3. Confirm version
kubectl exec -it coinjecture-node-0 -- /bin/sh -c "coinjectured --version"

# Expected: Previous version restored
```

**Rollback SLA:** < 5 minutes

---

## Post-Release Validation

### Validation Checklist

**Immediate (T+0h):**
- [ ] Canary deployment healthy (10% traffic)
- [ ] Parity validation 100% match rate
- [ ] Zero increase in error rate
- [ ] Metrics scraping successful
- [ ] Alerts not firing

**Short-term (T+24h):**
- [ ] Gradual rollout to 100% complete
- [ ] SLOs maintained (no budget exhaustion)
- [ ] Performance within expected range
- [ ] User-reported issues triaged
- [ ] Monitoring dashboards updated

**Long-term (T+7d):**
- [ ] Soak test complete (7-day stability)
- [ ] Zero regressions identified
- [ ] Release retrospective conducted
- [ ] Documentation updated
- [ ] Lessons learned documented

### Metrics to Monitor

**Golden Signals:**
- **Latency:** p50, p95, p99 request duration
- **Traffic:** Requests per second
- **Errors:** Error rate by endpoint/component
- **Saturation:** CPU, memory, disk utilization

**SLO-Specific:**
- Parity match rate (must stay 100%)
- IPFS pin quorum (must stay 100%)
- API availability (must stay ≥99.95%)
- Block validation latency (must stay within tier budgets)

---

## Release Calendar

### 2025 Release Schedule

| Version | Type | Branch Date | Release Date | Notes |
|---------|------|-------------|--------------|-------|
| v4.1.0 | Stable | 2025-11-04 | 2025-11-18 | Performance improvements |
| v4.2.0-rc.1 | RC | 2025-11-25 | 2025-12-02 | New features testing |
| v4.2.0 | Stable | 2025-12-02 | 2025-12-16 | Holiday freeze before 2025-12-20 |
| v5.0.0-alpha.1 | Alpha | 2026-01-06 | 2026-01-13 | Breaking changes preview |
| v4.3.0 | Stable | 2026-01-20 | 2026-02-03 | Bug fixes + backports |
| v5.0.0-lts | LTS | 2026-03-16 | 2026-04-01 | Annual LTS release |

**Freeze Windows:**
- **Holiday Freeze:** 2025-12-20 to 2026-01-05 (no production deploys)
- **Tax Season Freeze:** 2026-04-01 to 2026-04-20 (critical fixes only)

---

## Appendix: Checklists

### Pre-Release Checklist

```markdown
## Pre-Release Checklist: v4.1.0

**Release Manager:** @alice
**Target Date:** 2025-11-18

### Code Freeze (T-14d)
- [ ] Release branch created: `release/v4.1.0`
- [ ] Version bumped in all components
- [ ] CHANGELOG.md updated
- [ ] Golden vectors validated
- [ ] No open P0/P1 bugs

### Testing (T-7d)
- [ ] CI/CD passing (14/14 jobs green)
- [ ] Property tests: 10K examples, zero failures
- [ ] Fuzz tests: 6 hours, zero crashes
- [ ] Parity tests: 1K blocks, 100% match
- [ ] Determinism tests: Linux/macOS/Windows identical

### Security (T-3d)
- [ ] Vulnerability scan clean (0 critical, ≤2 high)
- [ ] License compliance verified
- [ ] SBOM generated and signed
- [ ] Security team sign-off

### Approval (T-1d)
- [ ] Release notes reviewed
- [ ] Approvals: RM, Platform Lead, Security, CTO
- [ ] Rollback plan documented
- [ ] On-call schedule confirmed

### Build & Sign (Release Day)
- [ ] Git tag created and pushed
- [ ] Artifacts built for all platforms
- [ ] Artifacts signed (Sigstore + GPG)
- [ ] Checksums generated and signed
- [ ] GitHub release created

### Deploy
- [ ] Canary deployment (10%)
- [ ] Monitoring: No alerts, SLOs green
- [ ] Gradual rollout to 100%
- [ ] Post-release validation complete

### Cleanup
- [ ] Merge release branch to main
- [ ] Close release issue
- [ ] Announce release (Slack, email, blog)
- [ ] Schedule retrospective
```

---

## References

- **Versioning:** https://semver.org/
- **Sigstore:** https://www.sigstore.dev/
- **CycloneDX:** https://cyclonedx.org/
- **SLSA Framework:** https://slsa.dev/
- **Supply Chain Levels for Software Artifacts (SLSA):** Level 3 target

---

**Document Control:**
- Version: 1.0.0
- Last Updated: 2025-11-04
- Next Review: 2025-12-01 (Quarterly)
- Approvers: Release Manager, CTO
- Status: ACTIVE
