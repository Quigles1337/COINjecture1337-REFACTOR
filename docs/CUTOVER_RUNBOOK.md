# Cutover Runbook: Legacy → Refactored Migration

**Version:** 4.0.0
**Status:** Active
**Owner:** @Quigles1337
**Last Updated:** 2025-11-04

## Overview

This runbook describes the **gradual cutover** strategy for migrating from legacy Python codec to institutional-grade Rust core with zero behavior drift.

## Feature Flag System

The `CODEC_MODE` environment variable controls the cutover strategy:

| Mode | Legacy | Refactored | Behavior | Use Case |
|------|--------|------------|----------|----------|
| `legacy_only` | ✅ | ❌ | Use only legacy | Pre-refactor baseline |
| `shadow` | ✅ | ✅ | Both run, log drifts | Initial testing |
| `refactored_primary` | Fallback | ✅ | Refactored first, fallback | Confidence building |
| `refactored_only` | ❌ | ✅ | Pure Rust | Post-cutover |

## Cutover Phases

### Phase 1: Baseline (Week 1)
**Goal:** Establish legacy performance baseline

```bash
export CODEC_MODE=legacy_only
# Run production workload for 7 days
# Collect metrics: throughput, latency, error rate
```

**Success Criteria:**
- [x] 7 days of stable operation
- [x] Baseline metrics collected
- [x] No incidents

### Phase 2: Shadow Mode (Week 2-3)
**Goal:** Validate refactored implementation in parallel

```bash
export CODEC_MODE=shadow
# Run both implementations
# Compare results
# Log any drifts
```

**Monitoring:**
```bash
# Start parity monitor
python python/tools/parity_monitor.py --log-file /var/log/coinjecture/parity.log

# Check stats every hour
python python/tools/parity_monitor.py --stats

# Alert on drift > 0.1%
python python/tools/parity_monitor.py --check-rollback --threshold 0.001
```

**Success Criteria:**
- [x] 100% parity (zero drifts detected)
- [x] Refactored performance >= legacy
- [x] 14 days continuous operation
- [x] All function types tested

**Rollback Trigger:**
- Drift rate > 0.1% for 1 hour
- Any consensus-critical function drift
- Performance regression > 20%

### Phase 3: Refactored Primary (Week 4-5)
**Goal:** Gradually shift traffic to refactored implementation

```bash
export CODEC_MODE=refactored_primary
# Use refactored by default
# Fallback to legacy on errors
```

**Traffic Split:**
- Week 4: 10% → 25% → 50% refactored
- Week 5: 75% → 90% → 100% refactored

**Monitoring:**
```bash
# Monitor error rates
watch -n 30 'grep "falling back to legacy" /var/log/coinjecture/app.log | tail -20'

# Check Prometheus
curl http://localhost:9090/api/v1/query?query=coinjecture_parity_drift_rate
```

**Success Criteria:**
- [x] < 0.01% fallback rate
- [x] Performance improvement validated
- [x] 14 days at 100% refactored primary
- [x] No legacy fallbacks for 48 hours

**Rollback Trigger:**
- Fallback rate > 1%
- Any data corruption detected
- Performance SLO violation

### Phase 4: Refactored Only (Week 6+)
**Goal:** Remove legacy code path entirely

```bash
export CODEC_MODE=refactored_only
# Pure Rust implementation
# No fallback available
```

**Validation:**
```bash
# Verify no legacy code paths hit
grep -r "legacy_fn" /var/log/coinjecture/ | wc -l  # Should be 0

# Run golden vector tests
cd rust/coinjecture-core
cargo test --test golden_tests

# Verify determinism
pytest python/tests/test_parity_validator.py
```

**Success Criteria:**
- [x] 30 days stable operation
- [x] All metrics green
- [x] Legacy code path removed
- [x] Performance improvement documented

## Monitoring Dashboards

### Grafana Dashboard: Cutover Health

**Panel 1: Parity Rate**
```promql
rate(coinjecture_parity_matches_total[5m])
/
(rate(coinjecture_parity_matches_total[5m]) + rate(coinjecture_parity_drifts_total[5m]))
```

**Panel 2: Performance Comparison**
```promql
histogram_quantile(0.95,
  rate(coinjecture_legacy_duration_ms_bucket[5m])
)
vs
histogram_quantile(0.95,
  rate(coinjecture_refactored_duration_ms_bucket[5m])
)
```

**Panel 3: Drift Rate by Function**
```promql
rate(coinjecture_parity_drifts_total[1h]) by (function)
```

### Alerts

**Critical: Parity Drift Detected**
```yaml
alert: ParityDrift
expr: rate(coinjecture_parity_drifts_total[5m]) > 0
for: 5m
severity: critical
annotations:
  summary: "Parity drift detected between legacy and refactored"
  description: "Function {{ $labels.function }} has drift rate {{ $value }}"
```

**Warning: Fallback Rate High**
```yaml
alert: HighFallbackRate
expr: rate(coinjecture_legacy_fallback_total[10m]) > 0.01
for: 10m
severity: warning
annotations:
  summary: "Refactored implementation fallback rate high"
  description: "Fallback rate: {{ $value | humanizePercentage }}"
```

## Rollback Procedures

### Automatic Rollback
```bash
# Check if rollback needed (runs every 5 min via cron)
*/5 * * * * python python/tools/parity_monitor.py --check-rollback --threshold 0.001 || \
  (echo "ROLLBACK TRIGGERED" && export CODEC_MODE=legacy_only && systemctl restart coinjecture)
```

### Manual Rollback
```bash
# Immediate rollback
export CODEC_MODE=legacy_only
systemctl restart coinjecture

# Verify rollback successful
python python/tools/parity_monitor.py --stats
```

### Post-Rollback Analysis
1. Collect logs for 1 hour before rollback
2. Identify root cause of drift
3. Fix in refactored implementation
4. Add regression test
5. Re-run shadow mode for 48 hours
6. Resume cutover

## Pre-Flight Checklist

Before starting cutover:

- [ ] All golden vector tests passing
- [ ] Determinism validated across platforms
- [ ] Strict decode tests passing (18/18)
- [ ] Parity monitor deployed and tested
- [ ] Grafana dashboards configured
- [ ] Alerts configured and tested
- [ ] Rollback procedures tested
- [ ] Incident commander identified
- [ ] Stakeholders notified

## Incident Response

### P0: Consensus Failure Detected
1. **STOP IMMEDIATELY** - Roll back to `legacy_only`
2. Isolate affected nodes
3. Capture state for forensics
4. Page on-call SRE + security team
5. Create incident ticket
6. Begin post-mortem within 4 hours

### P1: High Drift Rate (>0.1%)
1. Switch to `refactored_primary` (allows fallback)
2. Investigate drifting functions
3. Check for platform-specific issues
4. Review recent changes
5. Roll back if drift rate increases

### P2: Performance Regression
1. Compare p95/p99 latencies
2. Check resource utilization
3. Profile hot paths
4. Optimize if possible
5. Roll back if SLO violated

## Communication Plan

### Daily Standups (During Cutover)
- Parity stats review
- Performance comparison
- Any drifts detected
- Plan for next 24h

### Weekly Reports
- Cutover progress (% of traffic)
- Cumulative parity rate
- Performance improvements
- Issues encountered
- Next week's plan

### Stakeholder Updates
- Product: Weekly email
- Engineering: Slack #cutover channel
- Exec: Monthly summary

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Parity Rate | 100.00% | Prometheus |
| Drift Rate | < 0.001% | Parity monitor |
| Performance Improvement | > 20% | p95 latency |
| Fallback Rate | < 0.01% | Logs |
| Uptime | 99.9% | Grafana |
| Rollback Count | 0 | Manual tracking |

## Post-Cutover Tasks

- [ ] Remove legacy code (`git rm python/src/legacy/`)
- [ ] Update documentation
- [ ] Archive parity logs
- [ ] Write post-mortem (even if successful)
- [ ] Share learnings with team
- [ ] Celebrate! 🎉

## Emergency Contacts

- On-Call SRE: sre-oncall@example.com
- Incident Commander: @Quigles1337
- Security Team: security@example.com
- Product Owner: product@example.com

## References

- [Golden Vector Tests](../rust/coinjecture-core/golden/README.md)
- [Determinism CI](../.github/workflows/determinism.yml)
- [Parity Validator](../python/src/coinjecture/legacy_compat.py)
- [Parity Monitor Tool](../python/tools/parity_monitor.py)
- [Architecture Diagrams](../REFACTOR_ARCHITECTURE.md)

---

**Remember:** It's better to take 10 weeks and get it right than rush in 2 weeks and break consensus. When in doubt, roll back and investigate.
