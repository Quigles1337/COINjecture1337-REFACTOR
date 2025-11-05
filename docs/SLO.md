# Service Level Objectives (SLOs)

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** COINjecture Platform Team

---

## Table of Contents

1. [Overview](#overview)
2. [SLO Definitions](#slo-definitions)
3. [Measurement & Monitoring](#measurement--monitoring)
4. [Alert Thresholds](#alert-thresholds)
5. [Incident Response](#incident-response)
6. [Error Budgets](#error-budgets)

---

## Overview

This document defines Service Level Objectives (SLOs) for the COINjecture blockchain platform. These objectives represent **institutional-grade commitments** to reliability, performance, and correctness.

### SLO Philosophy

1. **Correctness over Speed**: We prioritize deterministic correctness over raw performance
2. **Zero Consensus Drift**: Any parity mismatch is a P0 incident
3. **Graceful Degradation**: Systems degrade predictably under load
4. **Observability First**: All SLOs must be measurable via Prometheus metrics

### Compliance Requirements

- **Financial Institution Grade**: 99.95% availability target
- **Determinism**: 100% hash parity across platforms
- **Data Integrity**: 100% IPFS pin quorum compliance
- **Security**: Zero tolerance for epoch replay attacks

---

## SLO Definitions

### 1. Availability SLOs

#### SLO-001: API Availability
**Objective:** API endpoints respond with HTTP 2xx/3xx within timeout
**Target:** 99.95% over rolling 30-day window
**Measurement Window:** 30 days
**Error Budget:** 21.6 minutes/month

**Exclusions:**
- Planned maintenance windows (announced 48h in advance)
- DDoS attacks (above rate limit thresholds)
- Upstream dependency failures (IPFS, network infrastructure)

**Prometheus Query:**
```promql
sum(rate(http_requests_total{code=~"2..|3.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

---

#### SLO-002: P2P Network Availability
**Objective:** P2P gossip network maintains ≥2/3 active peer connections
**Target:** 99.9% over rolling 7-day window
**Measurement Window:** 7 days
**Error Budget:** 10.08 minutes/week

**Prometheus Query:**
```promql
count(p2p_peer_status{status="active"})
/
count(p2p_peer_status) >= 0.67
```

---

#### SLO-003: IPFS Pinning Quorum
**Objective:** All blocks achieve ≥2/3 pin quorum within 60 seconds
**Target:** 100% (zero tolerance)
**Measurement Window:** Real-time
**Error Budget:** 0 failures

**Prometheus Query:**
```promql
ipfs_pin_quorum_success_ratio == 1.0
```

**Rationale:** SEC-005 requires pin quorum for consensus integrity. Any failure is a critical incident.

---

### 2. Performance SLOs

#### SLO-004: Block Validation Latency
**Objective:** 95th percentile block validation completes within budget limits
**Target:**
- **Mobile tier:** < 60 seconds (p95)
- **Desktop tier:** < 300 seconds (p95)
- **Workstation tier:** < 900 seconds (p95)
- **Server tier:** < 1800 seconds (p95)
- **Cluster tier:** < 3600 seconds (p95)

**Measurement Window:** 24 hours

**Prometheus Query:**
```promql
histogram_quantile(0.95,
  sum(rate(block_validation_duration_seconds_bucket[5m])) by (le, tier)
)
```

---

#### SLO-005: Header Hash Performance
**Objective:** Header hashing completes in < 1ms (p99)
**Target:** 99% of header hashes < 1ms
**Measurement Window:** 1 hour

**Prometheus Query:**
```promql
histogram_quantile(0.99,
  sum(rate(header_hash_duration_seconds_bucket[5m])) by (le)
) < 0.001
```

---

#### SLO-006: Merkle Root Performance
**Objective:** Merkle root computation scales linearly
**Target:**
- **100 transactions:** < 5ms (p95)
- **1,000 transactions:** < 50ms (p95)
- **10,000 transactions:** < 500ms (p95)

**Measurement Window:** 24 hours

**Prometheus Query:**
```promql
histogram_quantile(0.95,
  sum(rate(merkle_root_duration_seconds_bucket[5m])) by (le, tx_count_bucket)
)
```

---

### 3. Correctness SLOs

#### SLO-007: Parity Validation (Legacy vs Refactored)
**Objective:** 100% hash match rate between legacy Python and refactored Rust
**Target:** 100% (zero tolerance)
**Measurement Window:** Real-time
**Error Budget:** 0 mismatches

**Prometheus Query:**
```promql
dual_run_parity_match_rate == 1.0
```

**Alert Triggers:**
- Single mismatch: P0 page-out
- Automatic rollback if mismatch rate > 0.01% over 5 minutes

---

#### SLO-008: Cross-Platform Determinism
**Objective:** Identical hashes across Linux/macOS/Windows for same input
**Target:** 100% (zero tolerance)
**Measurement Window:** Daily CI runs
**Error Budget:** 0 divergences

**Measurement:**
- CI workflow runs daily at 00:00 UTC
- Tests 1,000 random BlockHeaders across 3 platforms
- Auto-comments on PRs if divergence detected

---

#### SLO-009: Epoch Replay Protection
**Objective:** Zero successful epoch replay attacks
**Target:** 100% detection rate
**Measurement Window:** Real-time
**Error Budget:** 0 successful replays

**Prometheus Query:**
```promql
sum(rate(epoch_replay_detected_total[5m]))
/
sum(rate(block_validation_attempts_total[5m]))
```

**Expected Behavior:**
- Replay attempts detected: WARN log, reject block
- Replay cache TTL: 7 days
- Persistence: Survives node restarts

---

### 4. Resource SLOs

#### SLO-010: Memory Usage
**Objective:** Consensus core memory stays within tier budget limits
**Target:**
- **Mobile:** < 256MB (p95)
- **Desktop:** < 1GB (p95)
- **Workstation:** < 4GB (p95)
- **Server:** < 16GB (p95)
- **Cluster:** < 64GB (p95)

**Measurement Window:** 24 hours

**Prometheus Query:**
```promql
process_resident_memory_bytes{component="consensus_core"}
<
tier_memory_budget_bytes
```

---

#### SLO-011: CPU Utilization
**Objective:** Steady-state CPU usage < 70% (allows burst capacity)
**Target:** 95% of 5-minute windows below 70% CPU
**Measurement Window:** 24 hours

**Prometheus Query:**
```promql
avg_over_time(process_cpu_seconds_total{component="consensus_core"}[5m]) < 0.70
```

---

#### SLO-012: Disk I/O
**Objective:** Replay cache persists without blocking validation
**Target:** Cache write latency < 10ms (p99)
**Measurement Window:** 1 hour

**Prometheus Query:**
```promql
histogram_quantile(0.99,
  sum(rate(cache_persist_duration_seconds_bucket[5m])) by (le)
) < 0.010
```

---

### 5. Security SLOs

#### SLO-013: Rate Limiting Effectiveness
**Objective:** Rate limiter rejects excess traffic without blocking legitimate requests
**Target:**
- False positive rate < 0.1% (legitimate requests blocked)
- True positive rate > 99% (malicious traffic blocked)

**Measurement Window:** 24 hours

**Prometheus Query:**
```promql
# False positive rate
sum(rate(rate_limit_false_positives_total[5m]))
/
sum(rate(http_requests_total[5m])) < 0.001

# True positive rate
sum(rate(rate_limit_blocked_total{reason="malicious"}[5m]))
/
sum(rate(rate_limit_blocked_total[5m])) > 0.99
```

---

#### SLO-014: Vulnerability Patching
**Objective:** Critical CVEs patched within 24 hours of disclosure
**Target:** 100% of CVSS ≥9.0 vulns patched within 24h
**Measurement Window:** Per-vulnerability

**Process:**
1. `cargo audit` / `pip-audit` / `govulncheck` runs on every commit
2. Critical vulns trigger P0 incident
3. Emergency patch + deploy within 24h
4. Post-mortem required

---

#### SLO-015: SBOM Freshness
**Objective:** SBOM generated on every release with valid signatures
**Target:** 100% of releases have signed SBOM within 1 hour of tag
**Measurement Window:** Per-release

**Verification:**
```bash
# Check SBOM exists
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/quigles1337/coinjecture:v4.1.0
```

---

## Measurement & Monitoring

### Prometheus Metrics

All SLOs are measured via Prometheus metrics exposed at:
- **Rust Core:** `http://localhost:9090/metrics`
- **Go Daemon:** `http://localhost:8080/metrics`
- **Python Shims:** `http://localhost:8001/metrics`

**Retention Policy:**
- High-resolution (15s): 7 days
- Low-resolution (5m): 90 days
- Aggregated (1h): 2 years

---

### Grafana Dashboards

**Dashboard 1: COINjecture Overview**
- File: `monitoring/grafana/dashboards/coinjecture-overview.json`
- Panels: Availability, Latency, Error Rate, Throughput
- Refresh: 30s

**Dashboard 2: Parity Validation**
- File: `monitoring/grafana/dashboards/parity-validation.json`
- Panels: Match Rate, Drift Detection, Codec Mode Distribution
- Refresh: 10s (real-time monitoring)

**Dashboard 3: Security & Compliance**
- File: `monitoring/grafana/dashboards/security-compliance.json`
- Panels: Epoch Replay, Rate Limiting, Pin Quorum, Vulnerability Scan Results
- Refresh: 1m

---

## Alert Thresholds

### P0 (Critical) - Page Immediately

| Alert | Condition | Threshold | Response Time |
|-------|-----------|-----------|---------------|
| **Parity Mismatch** | `dual_run_parity_match_rate < 1.0` | Single mismatch | Immediate rollback |
| **Pin Quorum Failure** | `ipfs_pin_quorum_success_ratio < 1.0` | Single failure | < 5 minutes |
| **Epoch Replay Bypass** | Successful replay attack | 1 successful bypass | Immediate investigation |
| **API Complete Outage** | `http_success_rate < 0.5` for 5m | 50% error rate | < 5 minutes |

---

### P1 (High) - Page During Business Hours

| Alert | Condition | Threshold | Response Time |
|-------|-----------|-----------|---------------|
| **SLO Budget Exhausted** | Error budget < 10% remaining | 90% budget used | < 1 hour |
| **Validation Latency Spike** | p95 latency > 2x tier budget | 2x expected time | < 2 hours |
| **Memory Leak Detected** | Memory growth > 10% per hour | Sustained growth | < 4 hours |
| **API Degraded** | `http_success_rate < 0.995` for 15m | Below SLO-001 | < 1 hour |

---

### P2 (Medium) - Ticket Created

| Alert | Condition | Threshold | Response Time |
|-------|-----------|-----------|---------------|
| **Cache Persist Slow** | p99 cache write > 100ms | 10x expected | Next business day |
| **Peer Churn High** | Peer disconnect rate > 10/min | High churn | Next business day |
| **CPU Utilization High** | CPU > 80% for 1 hour | Approaching saturation | Next business day |

---

### P3 (Low) - Monitor

| Alert | Condition | Threshold | Response Time |
|-------|-----------|-----------|---------------|
| **Dependency Update Available** | New stable version available | Non-critical update | Weekly review |
| **Cache Cleanup Needed** | Expired entries > 10,000 | Housekeeping needed | Weekly cleanup |
| **Dashboard Stale** | Last update > 1 week ago | Documentation drift | Monthly review |

---

## Incident Response

### Escalation Matrix

| Role | Contact | P0 | P1 | P2 | P3 |
|------|---------|----|----|----|----|
| **On-Call Engineer** | PagerDuty | Immediate | 1h | 1d | 1w |
| **Platform Lead** | Email + SMS | Immediate | 2h | 2d | - |
| **Security Team** | Slack #security | Immediate (SEC) | 4h | - | - |
| **Executive Sponsor** | Phone | Immediate (outage) | - | - | - |

---

### Post-Incident Review (PIR)

**Required for:**
- All P0 incidents
- P1 incidents with customer impact
- Any SLO breach > 50% of error budget

**Template:**
1. **Incident Summary** (2-3 sentences)
2. **Timeline** (Detection → Mitigation → Resolution)
3. **Root Cause Analysis** (5 Whys)
4. **Impact Assessment** (Users affected, revenue impact, data loss)
5. **Action Items** (Preventive measures, monitoring improvements)
6. **SLO Impact** (Error budget consumed, SLO breach duration)

**Publication:**
- Internal: Confluence within 48 hours
- External: Status page within 72 hours (if customer-impacting)

---

## Error Budgets

### Budget Calculation

**Formula:**
```
Error Budget = (1 - SLO Target) × Measurement Window
```

**Example (SLO-001: API Availability):**
- SLO Target: 99.95%
- Measurement Window: 30 days = 43,200 minutes
- Error Budget: (1 - 0.9995) × 43,200 = **21.6 minutes/month**

---

### Budget Tracking

**Prometheus Query:**
```promql
# Remaining error budget (minutes)
(1 - slo_target) * measurement_window_minutes
-
sum_over_time(slo_violations_minutes[30d])
```

**Visualization:**
- Grafana gauge: Green (> 50%), Yellow (10-50%), Red (< 10%)
- Burn rate alerts: Trigger P1 if burning > 2x expected rate

---

### Budget Policy

**When budget exhausted (< 0 minutes remaining):**

1. **Freeze Feature Rollouts**
   - No new feature flags enabled
   - No version bumps to `refactored_primary` or `refactored_only`
   - Focus shifts to reliability improvements

2. **Increase Monitoring**
   - Alert thresholds tightened by 50%
   - Dashboard refresh rates increased
   - Daily SLO review meetings

3. **Root Cause Analysis**
   - Mandatory PIR for budget exhaustion
   - Identify systemic issues (not one-off incidents)
   - Update SLO definitions if unrealistic

4. **Budget Reset**
   - Monthly reset on 1st of month at 00:00 UTC
   - Partial credit for over-achievement (max 10% carry-forward)

---

## SLO Review Process

### Quarterly Reviews (Every 90 days)

**Agenda:**
1. **Performance Analysis**
   - SLO achievement rate (% of time in-budget)
   - Trend analysis (improving/degrading)
   - Outlier incident investigation

2. **Target Adjustment**
   - Tighten targets if consistently over-achieving (> 95% in-budget)
   - Loosen targets if unrealistic (< 50% in-budget)
   - Align with business objectives

3. **Metric Validation**
   - Verify Prometheus queries capture intent
   - Check for measurement gaps
   - Add new SLOs for emerging risks

4. **Documentation Updates**
   - Update this document with new SLOs
   - Revise alert thresholds based on false positive rates
   - Publish quarterly SLO report

---

### Stakeholder Communication

**Monthly SLO Report (published 5th of each month):**
- Executive summary (1 page)
- SLO achievement scoreboard (Green/Yellow/Red)
- Error budget consumption trends
- Top 3 incidents by impact
- Upcoming reliability investments

**Recipients:**
- Platform engineering team
- Product management
- Executive leadership
- Customer success (if SLA-related)

---

## Appendix: Prometheus Alert Rules

**File:** `monitoring/prometheus/alerts.yml`

See complete alert rule definitions in the monitoring configuration files.

**Key Alert Groups:**
- `coinjecture.availability` (SLO-001 through SLO-003)
- `coinjecture.performance` (SLO-004 through SLO-006)
- `coinjecture.correctness` (SLO-007 through SLO-009)
- `coinjecture.resources` (SLO-010 through SLO-012)
- `coinjecture.security` (SLO-013 through SLO-015)

---

## References

- **RUNBOOKS.md** - Operational procedures for incident response
- **REFACTOR_ARCHITECTURE.md** - System architecture and security layers
- **CI/CD Workflows** - `.github/workflows/` for SLO validation in CI
- **Prometheus Documentation** - https://prometheus.io/docs/
- **Google SRE Book** - https://sre.google/sre-book/service-level-objectives/

---

**Document Control:**
- Version: 1.0.0
- Last Updated: 2025-11-04
- Next Review: 2025-02-04 (Quarterly)
- Approvers: Platform Engineering Lead, CTO
- Status: ACTIVE
