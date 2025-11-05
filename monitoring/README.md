# COINjecture Monitoring Stack

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Status:** Production-Ready

---

## Overview

This directory contains the complete observability stack for COINjecture, implementing institutional-grade monitoring aligned with our [SLO definitions](../docs/SLO.md).

### Stack Components

- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards
- **Alertmanager** - Alert routing and notification

### Key Features

✅ **15 SLOs** tracked in real-time
✅ **3 Grafana Dashboards** (Overview, Parity, Security)
✅ **50+ Alert Rules** across 8 severity categories
✅ **100% Observability** of consensus-critical paths
✅ **Zero-Blind-Spot** monitoring with dead man's switches

---

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose
- Access to COINjecture node metrics endpoints
- Port availability: 9090 (Prometheus), 3000 (Grafana), 9093 (Alertmanager)

### 1. Deploy Monitoring Stack

```bash
cd monitoring
docker-compose up -d
```

**Expected Services:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Alertmanager: http://localhost:9093

### 2. Configure Data Sources

Grafana dashboards are pre-configured to use the Prometheus data source. No manual configuration needed.

### 3. Import Dashboards

Dashboards are automatically provisioned from `grafana/dashboards/`:

1. **COINjecture - Platform Overview** (`coinjecture-overview`)
   - API availability, latency, throughput
   - Block validation performance
   - P2P network health
   - Error budget tracking

2. **COINjecture - Parity Validation** (`coinjecture-parity`)
   - Real-time parity match rate (SLO-007)
   - Drift detection and logging
   - Performance comparison (Rust vs Python)
   - Codec mode distribution

3. **COINjecture - Security & Compliance** (`coinjecture-security`)
   - Epoch replay protection (SEC-002)
   - IPFS pin quorum (SEC-005)
   - Rate limiting effectiveness
   - Vulnerability tracking

### 4. Configure Alerting

Edit `prometheus/alertmanager.yml` to configure notification channels:

```yaml
route:
  receiver: 'pagerduty-p0'
  routes:
    - match:
        severity: P0
      receiver: 'pagerduty-p0'
    - match:
        severity: P1
      receiver: 'slack-oncall'

receivers:
  - name: 'pagerduty-p0'
    pagerduty_configs:
      - service_key: '<YOUR_PAGERDUTY_KEY>'

  - name: 'slack-oncall'
    slack_configs:
      - api_url: '<YOUR_SLACK_WEBHOOK>'
        channel: '#coinjecture-alerts'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   COINjecture Nodes                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Rust Core    │  │ Go Daemon    │  │ Python Shims │  │
│  │ :9090/metrics│  │ :8080/metrics│  │ :8001/metrics│  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
└─────────┼─────────────────┼─────────────────┼───────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │      Prometheus (Scraper)      │
          │  - 15s scrape interval         │
          │  - 90d retention               │
          │  - 50+ alert rules             │
          └────────────┬───────────────────┘
                       │
          ┌────────────┴───────────────┐
          │                            │
          ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐
│      Grafana        │    │    Alertmanager     │
│  - 3 dashboards     │    │  - PagerDuty        │
│  - Auto-refresh     │    │  - Slack            │
│  - SLO tracking     │    │  - Email            │
└─────────────────────┘    └─────────────────────┘
```

---

## Metrics Catalog

### Consensus Core (Rust)

**Location:** `http://localhost:9090/metrics`

| Metric | Type | Description | SLO |
|--------|------|-------------|-----|
| `block_validation_duration_seconds` | Histogram | Block validation latency by tier | SLO-004 |
| `header_hash_duration_seconds` | Histogram | Header hash computation time | SLO-005 |
| `merkle_root_duration_seconds` | Histogram | Merkle root computation time | SLO-006 |
| `dual_run_parity_match_rate` | Gauge | Parity match rate (0-1) | SLO-007 |
| `dual_run_comparisons_total` | Counter | Total parity comparisons | SLO-007 |
| `dual_run_mismatches_total` | Counter | Total parity mismatches | SLO-007 |
| `epoch_replay_detected_total` | Counter | Replay attacks detected | SLO-009 |
| `epoch_replay_bypass_successful_total` | Counter | Replay bypasses (CRITICAL) | SLO-009 |
| `process_resident_memory_bytes` | Gauge | Memory usage by component | SLO-010 |
| `process_cpu_seconds_total` | Counter | CPU time used | SLO-011 |

### Go Daemon

**Location:** `http://localhost:8080/metrics`

| Metric | Type | Description | SLO |
|--------|------|-------------|-----|
| `http_requests_total` | Counter | HTTP requests by endpoint/code | SLO-001 |
| `http_request_duration_seconds` | Histogram | Request latency percentiles | SLO-001 |
| `p2p_peer_status` | Gauge | Peer count by status | SLO-002 |
| `ipfs_pin_quorum_success_ratio` | Gauge | IPFS pin quorum success (0-1) | SLO-003 |
| `ipfs_pin_success_total` | Counter | Successful pins by node | SLO-003 |
| `ipfs_pin_failure_total` | Counter | Failed pins by node | SLO-003 |
| `rate_limit_accepted_total` | Counter | Requests accepted | SLO-013 |
| `rate_limit_blocked_total` | Counter | Requests blocked by reason | SLO-013 |
| `rate_limit_false_positives_total` | Counter | False positive blocks | SLO-013 |

### Python Shims

**Location:** `http://localhost:8001/metrics`

| Metric | Type | Description | SLO |
|--------|------|-------------|-----|
| `dual_run_legacy_duration_seconds` | Histogram | Legacy Python latency | SLO-007 |
| `dual_run_refactored_duration_seconds` | Histogram | Refactored Rust latency | SLO-007 |
| `codec_mode_active` | Gauge | Active codec mode (0-3) | SLO-007 |
| `codec_mode_requests_total` | Counter | Requests by mode | SLO-007 |
| `cache_persist_duration_seconds` | Histogram | Cache write latency | SLO-012 |
| `epoch_replay_cache_size` | Gauge | Cache entry count | SLO-009 |

---

## SLO Dashboard Walkthrough

### 1. Platform Overview Dashboard

**Purpose:** High-level health and performance monitoring

**Key Panels:**
- **System Health** (top-left): Red/Green status based on critical SLOs
- **API Availability** (top): Real-time 99.95% SLO tracking
- **Parity Match Rate** (top): Must stay at 100% (any drift triggers P0)
- **IPFS Pin Quorum** (top): Must stay at 100% (consensus integrity)
- **API Request Rate** (middle): Traffic patterns by endpoint
- **Block Validation Latency** (middle): Performance by hardware tier
- **Error Budget Remaining** (bottom): 30-day budget consumption

**When to Use:**
- Daily operations check-in
- Incident response overview
- Weekly SLO reviews

**Alert Thresholds:**
- System Health < 1.0 → P0 page-out
- API Availability < 99.95% for 5m → P1 alert
- Error Budget < 10% → P2 alert (feature freeze warning)

---

### 2. Parity Validation Dashboard

**Purpose:** Real-time monitoring of dual-run validation (SLO-007)

**Key Panels:**
- **Parity Match Rate** (top-left): 100% required, 8 decimal precision
- **Total Comparisons** (top): Volume of dual-run validations
- **Total Mismatches** (top-right): CRITICAL if > 0
- **Active Codec Mode** (top): Feature flag state
- **Parity Match Rate Over Time** (middle): Trending with annotations
- **Performance Comparison** (bottom): Rust vs Python latency
- **Speedup Factor** (bottom-right): Rust performance gains

**When to Use:**
- During gradual rollout (shadow → refactored_primary)
- Post-deployment validation
- Performance regression testing
- Debugging drift detection

**Alert Thresholds:**
- Single mismatch → P0 immediate rollback
- Mismatch rate > 0.01% for 5m → Automatic rollback
- Speedup < 2x → P3 performance investigation

**Auto-Refresh:** 10 seconds (fastest refresh for critical SLO)

---

### 3. Security & Compliance Dashboard

**Purpose:** Security posture and compliance monitoring

**Key Panels:**
- **Security Posture Score** (top-left): Composite score (0-100)
- **Critical Vulns** (top): CVSS ≥9.0 count (must be 0)
- **Epoch Replays Detected** (top-right): Attack attempts
- **Rate Limiting Effectiveness** (middle): False positive tracking
- **Epoch Replay Events** (middle): Attack timeline
- **IPFS Pin Quorum** (middle): SEC-005 compliance
- **Vulnerability Scan Results** (bottom): By component/severity
- **Security Layer Rejections** (bottom): Defense-in-depth effectiveness

**When to Use:**
- Security reviews (weekly)
- Compliance audits
- Post-attack forensics
- Vulnerability remediation tracking

**Alert Thresholds:**
- Critical vuln detected → P0 page-out
- Replay bypass successful → P0 immediate investigation
- Pin quorum < 100% → P0 consensus integrity violation

**Auto-Refresh:** 1 minute

---

## Alert Response Procedures

### P0 Alerts (Page Immediately)

**1. Parity Mismatch Detected**
```
Alert: dual_run_parity_match_rate < 1.0
Response Time: Immediate
Action: Automatic rollback triggered
```

**Procedure:**
1. Rollback initiated automatically by alert webhook
2. Verify rollback success within 2 minutes
3. Check Grafana for mismatch details (function, input)
4. Create incident ticket: `INC-PARITY-YYYY-MM-DD-###`
5. Start PIR (Post-Incident Review)

**Runbook:** [docs/RUNBOOKS.md#parity-mismatch-rollback](../docs/RUNBOOKS.md#parity-mismatch-rollback)

---

**2. IPFS Pin Quorum Failure**
```
Alert: ipfs_pin_quorum_success_ratio < 1.0
Response Time: < 5 minutes
Action: Block propagation halted
```

**Procedure:**
1. Check IPFS node health: `docker ps | grep ipfs`
2. Check pin status by node in Grafana
3. If ≥2/3 nodes healthy: Continue with degraded quorum
4. If <2/3 nodes healthy: Halt block production
5. Investigate failed node logs
6. Restore quorum within 15 minutes

**Runbook:** [docs/RUNBOOKS.md#ipfs-pin-quorum-failure](../docs/RUNBOOKS.md#ipfs-pin-quorum-failure)

---

**3. Epoch Replay Bypass**
```
Alert: epoch_replay_bypass_successful_total > 0
Response Time: Immediate
Action: Security incident declared
```

**Procedure:**
1. Declare P0 security incident
2. Capture logs: `kubectl logs -l app=coinjecture --since=1h > incident.log`
3. Check replay cache integrity
4. Analyze commitment reuse pattern
5. Deploy emergency patch if exploit found
6. Notify security team + executive sponsor

**Runbook:** [docs/RUNBOOKS.md#security-incidents](../docs/RUNBOOKS.md#security-incidents)

---

### P1 Alerts (Page During Business Hours)

**SLO Budget Exhausted**
- Freeze feature rollouts
- Increase monitoring frequency
- Schedule PIR for budget exhaustion root cause

**Validation Latency Spike**
- Check resource utilization (CPU/memory)
- Review recent deployments for regressions
- Scale horizontally if needed

**Memory Leak Detected**
- Capture heap dump: `jemalloc` profiling
- Analyze allocation patterns
- Schedule restart within 4 hours if severe

---

## Troubleshooting

### Prometheus Not Scraping

**Symptoms:**
- `up{job="consensus_core"} == 0`
- Dashboards show "No data"

**Diagnosis:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# Check node metrics endpoint
curl http://localhost:9090/metrics | head -20
```

**Fix:**
1. Verify node is running and exposing metrics
2. Check firewall rules: `sudo iptables -L | grep 9090`
3. Verify Prometheus scrape config in `prometheus/prometheus.yml`
4. Restart Prometheus: `docker-compose restart prometheus`

---

### Grafana Dashboards Not Loading

**Symptoms:**
- Dashboards show "Panel plugin not found"
- Blank panels

**Diagnosis:**
```bash
# Check Grafana logs
docker logs grafana | tail -50

# Verify data source
curl -u admin:admin http://localhost:3000/api/datasources
```

**Fix:**
1. Verify Prometheus data source configured: `http://prometheus:9090`
2. Re-provision dashboards: `docker-compose restart grafana`
3. Clear browser cache and reload
4. Check JSON syntax in dashboard files

---

### Alerts Not Firing

**Symptoms:**
- SLO violation but no alert
- Alertmanager shows no active alerts

**Diagnosis:**
```bash
# Check Prometheus rules
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.state == "firing")'

# Check Alertmanager status
curl http://localhost:9093/api/v2/status
```

**Fix:**
1. Verify alert rule syntax: `promtool check rules prometheus/alerts.yml`
2. Check Alertmanager config: `amtool config show`
3. Verify notification channel credentials
4. Check alert inhibition rules (may be suppressing alerts)

---

## Customization

### Adding New Metrics

**1. Define Metric in Code**

**Rust (using `prometheus` crate):**
```rust
use prometheus::{Counter, Registry};

lazy_static! {
    static ref CUSTOM_COUNTER: Counter = Counter::new(
        "coinjecture_custom_total",
        "Custom metric description"
    ).unwrap();
}

pub fn register_metrics(registry: &Registry) {
    registry.register(Box::new(CUSTOM_COUNTER.clone())).unwrap();
}

// Increment metric
CUSTOM_COUNTER.inc();
```

**Go (using `prometheus/client_golang`):**
```go
import "github.com/prometheus/client_golang/prometheus"

var customCounter = prometheus.NewCounter(prometheus.CounterOpts{
    Name: "coinjecture_custom_total",
    Help: "Custom metric description",
})

func init() {
    prometheus.MustRegister(customCounter)
}

// Increment metric
customCounter.Inc()
```

**2. Add to Prometheus Scrape**

Prometheus automatically scrapes all metrics from configured endpoints. No config change needed.

**3. Create Grafana Panel**

```json
{
  "targets": [
    {
      "expr": "rate(coinjecture_custom_total[5m])",
      "legendFormat": "Custom Metric",
      "refId": "A"
    }
  ]
}
```

---

### Adding New Alerts

**1. Define Alert Rule**

Edit `prometheus/alerts.yml`:

```yaml
- name: coinjecture.custom
  interval: 1m
  rules:
    - alert: CustomThresholdExceeded
      expr: coinjecture_custom_total > 1000
      for: 5m
      labels:
        severity: P2
        component: custom
      annotations:
        summary: "Custom threshold exceeded"
        description: "Value: {{ $value }}. Threshold: 1000"
        runbook: "https://github.com/.../docs/RUNBOOKS.md#custom"
```

**2. Validate Syntax**

```bash
promtool check rules prometheus/alerts.yml
```

**3. Reload Prometheus**

```bash
curl -X POST http://localhost:9090/-/reload
```

**4. Test Alert**

```bash
# Trigger condition
# Wait for `for: 5m` duration
# Check Alertmanager
curl http://localhost:9093/api/v2/alerts
```

---

### Creating Custom Dashboards

**1. Design in Grafana UI**

1. Navigate to http://localhost:3000
2. Create → Dashboard
3. Add panels with desired queries
4. Configure thresholds, legends, colors
5. Save dashboard

**2. Export JSON**

1. Dashboard Settings → JSON Model
2. Copy JSON
3. Save to `grafana/dashboards/custom-dashboard.json`

**3. Provision Dashboard**

Edit `grafana/provisioning/dashboards/dashboards.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'COINjecture Dashboards'
    folder: 'COINjecture'
    type: file
    options:
      path: /etc/grafana/dashboards
```

Place JSON in `grafana/dashboards/` and restart:

```bash
docker-compose restart grafana
```

---

## Production Deployment

### High Availability Setup

**Architecture:**
```
┌─────────────────────────────────────┐
│     Load Balancer (HAProxy)         │
│      (Prometheus Federation)        │
└────────────┬────────────────────────┘
             │
   ┌─────────┴─────────┬──────────────┐
   │                   │              │
   ▼                   ▼              ▼
┌──────────┐     ┌──────────┐  ┌──────────┐
│Prometheus│     │Prometheus│  │Prometheus│
│  Shard 1 │     │  Shard 2 │  │  Shard 3 │
│ (Node 1) │     │ (Node 2) │  │ (Node 3) │
└──────────┘     └──────────┘  └──────────┘
```

**1. Deploy Prometheus Federation**

`prometheus-federation.yml`:
```yaml
scrape_configs:
  - job_name: 'federate'
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="consensus_core"}'
        - '{job="go_daemon"}'
    static_configs:
      - targets:
        - 'prometheus-shard-1:9090'
        - 'prometheus-shard-2:9090'
        - 'prometheus-shard-3:9090'
```

**2. Configure Grafana for HA**

Use shared PostgreSQL backend:

```yaml
database:
  type: postgres
  host: postgres:5432
  name: grafana
  user: grafana
  password: ${GF_DATABASE_PASSWORD}
```

**3. Alertmanager Clustering**

```yaml
alertmanager:
  cluster:
    listen-address: "0.0.0.0:9094"
    peers:
      - alertmanager-1:9094
      - alertmanager-2:9094
      - alertmanager-3:9094
```

---

### Long-Term Storage

**Option 1: Thanos**

```yaml
# thanos-sidecar.yml
- name: thanos-sidecar
  image: quay.io/thanos/thanos:v0.32.0
  args:
    - sidecar
    - --tsdb.path=/prometheus
    - --objstore.config-file=/etc/thanos/bucket.yml
    - --prometheus.url=http://localhost:9090
```

**Option 2: Cortex**

```yaml
# cortex.yml
storage:
  engine: blocks

blocks_storage:
  backend: s3
  s3:
    bucket_name: coinjecture-metrics
    endpoint: s3.amazonaws.com
```

---

## Security Hardening

### 1. Enable Authentication

**Prometheus:**
```yaml
# prometheus.yml
basic_auth_users:
  admin: $2y$10$... # bcrypt hash
```

**Grafana:**
```ini
# grafana.ini
[auth]
disable_login_form = false
disable_signout_menu = false

[auth.basic]
enabled = true

[security]
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
secret_key = ${GF_SECURITY_SECRET_KEY}
```

### 2. Enable TLS

**Nginx reverse proxy:**
```nginx
server {
    listen 443 ssl http2;
    server_name metrics.coinjecture.io;

    ssl_certificate /etc/ssl/certs/coinjecture.crt;
    ssl_certificate_key /etc/ssl/private/coinjecture.key;

    location / {
        proxy_pass http://grafana:3000;
        proxy_set_header Host $host;
    }
}
```

### 3. Network Segmentation

```yaml
# docker-compose.yml
networks:
  monitoring:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
    internal: true  # No external access
```

---

## Performance Tuning

### Prometheus

**Optimize Scrape Intervals:**
```yaml
global:
  scrape_interval: 15s  # Default

scrape_configs:
  - job_name: 'consensus_core'
    scrape_interval: 5s  # High-frequency for critical metrics

  - job_name: 'logs'
    scrape_interval: 60s  # Low-frequency for less critical
```

**Increase Retention:**
```yaml
# prometheus.yml
storage:
  tsdb:
    retention.time: 90d
    retention.size: 100GB
```

### Grafana

**Enable Query Caching:**
```ini
# grafana.ini
[dataproxy]
timeout = 30
keep_alive_seconds = 30

[caching]
enabled = true
```

**Optimize Dashboard Queries:**
- Use recording rules for expensive queries
- Limit time range to necessary window
- Use `rate()` instead of `increase()` for smoother graphs

---

## Reference

- **SLO Definitions:** [../docs/SLO.md](../docs/SLO.md)
- **Operational Runbooks:** [../docs/RUNBOOKS.md](../docs/RUNBOOKS.md)
- **Architecture:** [../REFACTOR_ARCHITECTURE.md](../REFACTOR_ARCHITECTURE.md)
- **Prometheus Docs:** https://prometheus.io/docs/
- **Grafana Docs:** https://grafana.com/docs/
- **SRE Book (Google):** https://sre.google/sre-book/monitoring-distributed-systems/

---

**Maintained by:** COINjecture Platform Team
**Support:** #coinjecture-platform (Slack)
**On-Call:** PagerDuty rotation
