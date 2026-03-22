# Performance Metrics - Prometheus & Grafana Integration

## 📋 Overview

**Performance Metrics** adalah dashboard monitoring real-time untuk Aldudu Academy yang terintegrasi dengan **Prometheus** (metrics collection) dan **Grafana** (visualization).

---

## 🎯 Features

### **1. Super Admin Dashboard** (`/superadmin/metrics`)

#### **Real-Time Metrics:**
- 📊 **CPU Usage** - Processor utilization
- 📊 **Memory Usage** - RAM consumption (GB & %)
- 📊 **Disk Usage** - Storage utilization
- 📊 **Active Users** - Currently active users

#### **Application Metrics:**
- 👥 **Users by Role** - Breakdown (Super Admin, Admin, Guru, Murid)
- 🏫 **Schools Statistics** - Active, Pending, Suspended
- 📚 **Courses** - Total courses created
- 📝 **Business Metrics** - Students enrolled, Quizzes taken

#### **Prometheus Integration:**
- ✓ Metrics endpoint: `/metrics`
- ✓ Custom metrics: `aldudu_requests_total`, `aldudu_request_latency_seconds`
- ✓ Auto-scraping every 15 seconds
- ✓ Business metrics tracking

#### **Quick Actions:**
- 🔗 Access Prometheus UI (`/metrics`)
- 🔗 Access Grafana Dashboard (`http://localhost:3000`)
- 🔄 Refresh Metrics
- 📥 Export Metrics (JSON)

---

### **2. Prometheus Metrics Server**

#### **System Metrics (Node Exporter):**
- CPU per-core usage
- Memory (RAM, Swap)
- Disk I/O operations
- Network traffic
- Filesystem usage

#### **Application Metrics (Flask Exporter):**
- HTTP request rate (by endpoint, method, status)
- Request latency (Histogram with P50, P95, P99)
- Active users gauge
- Business metrics (courses, quizzes, students)

#### **Custom Metrics:**
```prometheus
# Total requests
aldudu_requests_total{method, endpoint, status}

# Request latency
aldudu_request_latency_seconds_bucket{method, endpoint}
aldudu_request_latency_seconds_count{method, endpoint}
aldudu_request_latency_seconds_sum{method, endpoint}

# Active users
aldudu_active_users

# Business metrics
aldudu_courses_created_total
aldudu_quizzes_taken_total
aldudu_students_enrolled
```

---

### **3. Grafana Dashboards**

#### **Pre-configured Panels:**
1. **Stat Panels:**
   - Active Users
   - Monitored Endpoints
   - Success Rate
   - P95 Latency

2. **Time Series Charts:**
   - Request Rate by Endpoint
   - Request Latency (P50, P95)
   - CPU Usage
   - Memory Usage
   - Disk Usage

3. **Features:**
   - Auto-refresh every 10 seconds
   - Custom time range selection
   - Export graphs (PNG, CSV, PDF)
   - Alert configuration
   - Annotations support

---

## 📦 Installation

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

New dependencies:
- `prometheus-client==0.20.0` - Prometheus Python client
- `prometheus-flask-exporter==0.23.1` - Flask metrics exporter

---

### **2. Start Monitoring Stack**

```bash
# Navigate to deploy directory
cd deploy

# Start Prometheus & Grafana
docker compose -f docker-compose.monitoring.yml up -d
```

**Services:**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Node Exporter**: http://localhost:9100

---

### **3. Access Grafana**

**Default Credentials:**
- **URL**: http://localhost:3000
- **Username**: `admin`
- **Password**: `admin123`

**Pre-configured:**
- ✓ Prometheus datasource (auto-connected)
- ✓ Aldudu Academy dashboard (auto-imported)
- ✓ Refresh every 10 seconds

---

## 🔧 Configuration

### **Environment Variables (.env)**

```env
# Prometheus Metrics
PROMETHEUS_ENABLED=true

# Optional: Customize scrape interval in deploy/prometheus.yml
```

### **Prometheus Configuration**

File: `deploy/prometheus.yml`

```yaml
global:
  scrape_interval: 15s  # How often to scrape metrics
  
scrape_configs:
  - job_name: 'aldudu-academy'
    static_configs:
      - targets: ['host.docker.internal:5000']
    metrics_path: '/metrics'
```

**Important:** 
- `host.docker.internal` allows Docker to access host machine
- Flask app must be running on port 5000

---

## 🎯 Usage

### **Access Performance Metrics Dashboard**

1. **Login** as Super Admin
2. **Navigate** to: **Sistem → Performance Metrics**
3. **URL**: `http://localhost:5000/superadmin/metrics`

### **View Raw Prometheus Metrics**

Open browser: `http://localhost:5000/metrics`

Example output:
```prometheus
# HELP aldudu_requests_total Total requests
# TYPE aldudu_requests_total counter
aldudu_requests_total{endpoint="/login",method="POST",status="200"} 150.0

# HELP aldudu_request_latency_seconds Request latency
# TYPE aldudu_request_latency_seconds histogram
aldudu_request_latency_seconds_bucket{endpoint="/api/data",le="0.1"} 100.0
```

### **Access Grafana Dashboard**

1. Open: http://localhost:3000
2. Login: `admin` / `admin123`
3. Dashboard: **Aldudu Academy Dashboard** (auto-loaded)

---

## 📊 API Endpoints

### **Get Metrics Data**
```
GET /superadmin/api/metrics/data
```

Response:
```json
{
  "success": true,
  "metrics": {
    "system": {
      "cpu_percent": 45.2,
      "memory_percent": 62.5,
      "memory_used_gb": 8.5,
      "memory_total_gb": 16.0,
      "disk_percent": 55.0,
      "disk_used_gb": 220.5,
      "disk_total_gb": 500.0
    },
    "application": {
      "active_users": 342,
      "total_requests": 15420,
      "avg_latency_ms": 45,
      "error_rate": 0.02
    },
    "users": {
      "total": 1500,
      "by_role": {
        "super_admin": 5,
        "admin": 10,
        "guru": 200,
        "murid": 1285
      }
    },
    "business": {
      "courses": 300,
      "students_enrolled": 1285,
      "quizzes_taken": 5420
    },
    "prometheus": {
      "enabled": true,
      "endpoint": "/metrics"
    }
  }
}
```

### **Refresh Metrics**
```
POST /superadmin/api/metrics/refresh
```

---

## 🚨 Alerting (Optional)

### **Configure Alerts in Grafana**

1. **Open Dashboard** in Grafana
2. **Click** on panel title → **Edit**
3. **Alert** tab → **Create Alert**
4. **Configure:**
   - Condition: `WHEN last() OF query(A, 5m, now) IS ABOVE 80`
   - Notifications: Email, Slack, Webhook

### **Example Alert Rules:**

```yaml
# Add to prometheus.yml
groups:
  - name: aldudu-alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes"

      - alert: HighErrorRate
        expr: sum(rate(aldudu_requests_total{status=~"5.."}[5m])) / sum(rate(aldudu_requests_total[5m])) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5%"
```

---

## 📁 File Structure

```
aldudu-academy/
├── app/
│   ├── __init__.py              # Prometheus metrics initialization
│   └── templates/
│       └── superadmin/
│           └── metrics.html      # Performance Metrics dashboard
├── deploy/
│   ├── docker-compose.monitoring.yml  # Prometheus & Grafana stack
│   ├── prometheus.yml                # Prometheus configuration
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── datasources.yml   # Auto-configured Prometheus datasource
│       │   └── dashboards/
│       │       └── dashboards.yml    # Dashboard provisioning
│       └── dashboards/
│           └── aldudu-academy.json   # Pre-built Grafana dashboard
└── requirements.txt
```

---

## 🔍 Metrics Reference

### **System Metrics (Node Exporter)**

| Metric | Description |
|--------|-------------|
| `node_cpu_seconds_total` | CPU time spent in each mode |
| `node_memory_MemAvailable_bytes` | Available memory |
| `node_memory_MemTotal_bytes` | Total memory |
| `node_filesystem_avail_bytes` | Available filesystem space |
| `node_filesystem_size_bytes` | Total filesystem size |
| `node_network_receive_bytes_total` | Network bytes received |
| `node_network_transmit_bytes_total` | Network bytes transmitted |

### **Application Metrics (Flask)**

| Metric | Description | Labels |
|--------|-------------|--------|
| `aldudu_requests_total` | Total HTTP requests | `method`, `endpoint`, `status` |
| `aldudu_request_latency_seconds` | Request latency histogram | `method`, `endpoint` |
| `aldudu_active_users` | Current active users | - |
| `aldudu_courses_created_total` | Total courses created | - |
| `aldudu_quizzes_taken_total` | Total quizzes taken | - |
| `aldudu_students_enrolled` | Currently enrolled students | - |

---

## 🛠️ Troubleshooting

### **Prometheus Cannot Scrape Flask App**

**Problem:** `target down` in Prometheus

**Solutions:**
1. Ensure Flask app is running: `python run.py`
2. Check `/metrics` endpoint: `curl http://localhost:5000/metrics`
3. Verify `host.docker.internal` in `prometheus.yml`
4. For Linux, add to `/etc/hosts`: `127.0.0.1 host.docker.internal`

### **Grafana Dashboard Not Showing**

**Problem:** Dashboard not auto-imported

**Solutions:**
1. Check provisioning logs: `docker logs aldudu-grafana`
2. Verify file permissions in `deploy/grafana/dashboards/`
3. Manually import: Grafana UI → Dashboards → Import → Upload JSON

### **No Metrics Data**

**Problem:** Dashboard shows empty graphs

**Solutions:**
1. Wait 1-2 minutes for Prometheus to scrape data
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify Flask app has `PROMETHEUS_ENABLED=true`
4. Check Flask logs for errors

### **High Memory Usage**

**Problem:** Prometheus using too much memory

**Solutions:**
1. Reduce retention: `--storage.tsdb.retention.time=7d` in `docker-compose.monitoring.yml`
2. Reduce scrape interval: Change `scrape_interval: 30s` in `prometheus.yml`
3. Add metric relabeling to drop unused metrics

---

## 🔐 Security Notes

### **Production Deployment**

1. **Change Default Passwords:**
   ```yaml
   environment:
     - GF_SECURITY_ADMIN_USER=your-username
     - GF_SECURITY_ADMIN_PASSWORD=your-strong-password
   ```

2. **Enable Authentication:**
   - Grafana: Already enabled by default
   - Prometheus: Add basic auth via Nginx reverse proxy

3. **Restrict Access:**
   - `/metrics` endpoint should be internal only
   - Use firewall rules to limit access to Prometheus/Grafana

4. **HTTPS:**
   - Configure SSL/TLS for Grafana
   - Use reverse proxy (Nginx/Traefik)

---

## 📊 Grafana Screenshot

**Dashboard Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  Aldudu Academy Dashboard                      [Refresh]   │
├────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  Active  │ │ Endpoints│ │ Success  │ │   P95        │  │
│  │  Users   │ │          │ │   Rate   │ │   Latency    │  │
│  │   342    │ │    25    │ │  99.8%   │ │    45ms      │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│                                                             │
│  ┌─────────────────────┐ ┌────────────────────────────────┐│
│  │  Request Rate       │ │     Request Latency            ││
│  │  [Time Series]      │ │     [Time Series P50/P95]      ││
│  └─────────────────────┘ └────────────────────────────────┘│
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │   CPU    │ │  Memory  │ │   Disk   │                    │
│  │  [TS]    │ │   [TS]   │ │   [TS]   │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Flask app
python run.py

# 3. Start monitoring stack (in new terminal)
cd deploy
docker compose -f docker-compose.monitoring.yml up -d

# 4. Access dashboards
# - Super Admin: http://localhost:5000/superadmin/metrics
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin123)
```

---

## 📚 References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Flask Exporter](https://github.com/rycus86/prometheus_flask_exporter)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter)

---

**Created**: 2026-03-22  
**Version**: 1.0.0  
**Author**: Aldudu Academy Dev Team
