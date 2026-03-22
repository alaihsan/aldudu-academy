# Health Status Dashboard with Sentry Integration

## 📋 Overview

Fitur **Health Status Dashboard** untuk monitoring kondisi aplikasi Aldudu Academy secara keseluruhan, terintegrasi dengan **Sentry** untuk error tracking.

---

## 🚀 Features

### 1. **System Health Checks**
Real-time monitoring untuk semua layanan:
- ✅ **Database** - MySQL/PostgreSQL connection status
- ✅ **Redis/Celery** - Message broker status
- ✅ **Email Service** - SMTP configuration
- ✅ **Sentry** - Error tracking status
- ✅ **Storage** - Write permissions check

### 2. **Application Statistics**
- Total users breakdown by role (Super Admin, Admin, Guru, Murid)
- Sekolah statistics (Active, Pending, Suspended)
- Content statistics (Courses, Quizzes, Assignments)
- Activity logs (last 24 hours)
- System info (Python version, Platform)

### 3. **Sentry Integration**
- Automatic error tracking
- Performance monitoring (APM)
- Python profiling
- Release tracking

### 4. **Quick Actions**
- Test email configuration
- Clear cache (fully implemented)
- Access Sentry dashboard

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies:
- `sentry-sdk[flask]==2.20.0` - Error tracking
- `psutil==6.1.0` - System utilities

### 2. Configure Sentry

1. **Create Sentry Account**: Go to [https://sentry.io](https://sentry.io)
2. **Create New Project**: Select Flask framework
3. **Copy DSN**: Get your project DSN from Settings → Client Keys

### 3. Update Environment Variables (Optional)

Edit `.env` file to override default settings:

```env
# Sentry Configuration
# Default DSN is already configured. Add this only if you want to use your own DSN.
SENTRY_DSN=https://your-sentry-dsn@sentry.io/your-project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_RELEASE=aldudu-academy@1.0.0
```

**Default Configuration:**
- **DSN**: `https://f62390a07b26a64ee235921994078f43@o4511087650734080.ingest.de.sentry.io/4511087662530640`
- **PII Enabled**: Yes (sends user data like IP, headers)
- **Trace Sample Rate**: 10%
- **Profile Sample Rate**: 10%
- **Environment**: Auto-detected (development/production)

---

## 🎯 Usage

### Access Health Dashboard

1. Login as **Super Admin**
2. Navigate to **Sistem → Health Status**
3. URL: `http://localhost:5000/superadmin/health`

### Dashboard Features

#### **System Health Cards**
- Shows status of all services (Healthy/Warning/Down)
- Response time for each service
- Auto-refresh every 30 seconds

#### **Statistics Cards**
- Total Users
- Active Schools
- Pending Schools
- Suspended Schools

#### **Users by Role**
Breakdown of users by role with color-coded badges

#### **Environment Info**
- Python version
- Platform
- Database info
- Total schools

#### **Quick Actions**
- **Test Email**: Send test email to verify SMTP
- **Clear Cache**: Flush application cache (school slug cache, rate limits, session cache)
- **Sentry Dashboard**: Open Sentry.io in new tab

---

## 🔌 API Endpoints

### Health Checks
```
GET /superadmin/api/health/checks
```

Response:
```json
{
  "success": true,
  "overall_healthy": true,
  "checks": {
    "database": {
      "status": "healthy",
      "response_time": "12.34ms",
      "message": "Database connection OK"
    },
    "redis": {
      "status": "healthy",
      "response_time": "5.67ms",
      "message": "Redis connection OK"
    },
    "email": {
      "status": "healthy",
      "response_time": "23.45ms",
      "message": "Mail server: sandbox.smtp.mailtrap.io"
    },
    "sentry": {
      "status": "healthy",
      "message": "Sentry configured",
      "dsn": "https://your-sentry-dsn..."
    },
    "storage": {
      "status": "healthy",
      "message": "Write permission OK: instance"
    }
  },
  "timestamp": "2026-03-22 17:00:00"
}
```

### Application Statistics
```
GET /superadmin/api/health/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "users": {
      "total": 1500,
      "by_role": {
        "super_admin": 5,
        "admin": 10,
        "guru": 200,
        "murid": 1285
      }
    },
    "schools": {
      "total": 50,
      "active": 45,
      "pending": 3,
      "suspended": 2
    },
    "content": {
      "courses": 300,
      "quizzes": 1200,
      "assignments": 800
    },
    "activity": {
      "last_24h": 5420
    },
    "system": {
      "python_version": "3.12.0",
      "platform": "win32"
    }
  }
}
```

### Test Email
```
POST /superadmin/api/health/test-email
```

Request:
```json
{
  "email": "test@example.com"
}
```

### Clear Cache
```
POST /superadmin/api/health/clear-cache
```

Response:
```json
{
  "success": true,
  "message": "Cache berhasil dibersihkan",
  "details": "Semua data cache telah dihapus"
}
```

**What gets cleared:**
- School slug cache (memoized function cache)
- Rate limit counters
- Session cache
- Any other Flask-Caching data

---

## 🛠️ Sentry Features

### Automatic Tracking

Sentry automatically tracks:
- ✅ Uncaught exceptions
- ✅ Flask request errors
- ✅ Database query errors
- ✅ Redis errors
- ✅ Performance bottlenecks

### Manual Error Tracking

```python
import sentry_sdk
from sentry_sdk import capture_exception, capture_message

# Capture exception
try:
    risky_operation()
except Exception as e:
    capture_exception(e)

# Capture message
capture_message("Something important happened")

# Add context
with sentry_sdk.configure_scope() as scope:
    scope.set_tag("custom_tag", "value")
    scope.user = {"email": "user@example.com"}
```

### Performance Monitoring

```python
from sentry_sdk import start_transaction

with start_transaction(op="task", name="Custom Operation"):
    # Your code here
    perform_task()
```

---

## 📁 Files Modified/Created

### Modified Files
- `requirements.txt` - Added Sentry SDK & psutil
- `app/__init__.py` - Sentry configuration & health routes
- `app/templates/superadmin/base.html` - Added Health Status menu
- `.env copy.example` - Added Sentry environment variables

### New Files
- `app/templates/superadmin/health.html` - Health dashboard UI

---

## 🔧 Troubleshooting

### Sentry Not Sending Events

1. **Check DSN**: Verify `SENTRY_DSN` in `.env` is correct
2. **Network**: Ensure server can reach `sentry.io`
3. **Sample Rate**: Check `SENTRY_TRACES_SAMPLE_RATE` > 0
4. **Firewall**: Whitelist `*.sentry.io`

### Health Checks Failing

1. **Database**: Check `DATABASE_URL` connection string
2. **Redis**: Ensure Redis server is running
3. **Email**: Verify Mailtrap/SMTP credentials
4. **Storage**: Check `instance/` folder permissions

### Performance Issues

Reduce sample rates in `.env`:
```env
SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% instead of 10%
SENTRY_PROFILES_SAMPLE_RATE=0.05
```

---

## 📊 Sentry Dashboard

Access your Sentry dashboard at: **https://sentry.io**

### Key Metrics to Monitor

1. **Error Rate**: Errors per hour/day
2. **Performance**: Average response time
3. **Cold Starts**: Function initialization time
4. **User Impact**: How many users affected

### Setting Up Alerts

1. Go to **Project Settings → Alerts**
2. Create new alert rule:
   - **Condition**: `error.count() > 10` in 5 minutes
   - **Action**: Email/Slack notification
3. Save and test

---

## 🎨 UI Preview

The Health Status dashboard features:
- Clean, modern card-based layout
- Color-coded status indicators
- Real-time auto-refresh (30s)
- Responsive design
- Interactive quick actions

---

## 🔐 Security Notes

- Health dashboard only accessible by **Super Admin**
- Sentry DSN is public (client-side) - this is by design
- Sensitive data is filtered by Sentry automatically
- Use `SENTRY_TRACES_SAMPLE_RATE` to control data volume

---

## 📚 References

- [Sentry Python SDK Docs](https://docs.sentry.io/platforms/python/)
- [Sentry Flask Integration](https://docs.sentry.io/platforms/python/integrations/flask/)
- [Sentry Performance Monitoring](https://docs.sentry.io/product/performance/)

---

**Created**: 2026-03-22  
**Version**: 1.0.0  
**Author**: Aldudu Academy Dev Team
