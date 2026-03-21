# 📡 Rasch Model API Reference

## Base URL

```
/api/rasch
```

## Authentication

Semua endpoint memerlukan authentication via Flask-Login. User harus login sebagai:
- **Guru**: Untuk mengakses analisis quiz yang diajar
- **Siswa**: Untuk mengakses ability measure sendiri
- **Super Admin**: Akses penuh ke semua analisis

---

## Threshold & Trigger Endpoints

### GET `/quizzes/:id/threshold-status`

Check threshold progress untuk quiz.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Quiz ID |

**Response:**
```json
{
  "success": true,
  "quiz_id": 123,
  "total_students": 45,
  "submitted": 28,
  "min_required": 30,
  "threshold_met": false,
  "remaining": 2,
  "percentage": 93.3,
  "auto_trigger_enabled": true,
  "status": "waiting",
  "message": "Menunggu 2 siswa lagi untuk memulai analisis Rasch"
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Quiz tidak ditemukan

**Example:**
```bash
curl http://localhost:5000/api/rasch/quizzes/123/threshold-status
```

---

### POST `/quizzes/:id/analyze`

Manual trigger Rasch analysis (bypass threshold).

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Quiz ID |
| min_persons | integer | body | No | Override minimum persons |

**Request Body:**
```json
{
  "min_persons": 20
}
```

**Response:**
```json
{
  "success": true,
  "message": "Rasch analysis started"
}
```

**Status Codes:**
- `200 OK`: Analysis triggered successfully
- `400 Bad Request`: Rasch not enabled atau error lainnya
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Quiz tidak ditemukan

**Example:**
```bash
curl -X POST http://localhost:5000/api/rasch/quizzes/123/analyze \
  -H "Content-Type: application/json" \
  -d '{"min_persons": 20}'
```

---

## Analysis Management Endpoints

### GET `/analyses`

List all analyses dengan filtering.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| course_id | integer | query | No | Filter by course |
| quiz_id | integer | query | No | Filter by quiz |
| status | string | query | No | Filter by status |

**Valid Status Values:**
- `pending`
- `waiting`
- `queued`
- `processing`
- `completed`
- `failed`
- `partial`

**Response:**
```json
{
  "success": true,
  "analyses": [
    {
      "id": 1,
      "course_id": 1,
      "quiz_id": 123,
      "name": "Mid Term Exam Analysis",
      "analysis_type": "quiz",
      "status": "completed",
      "progress_percentage": 100.0,
      "num_persons": 45,
      "num_items": 30,
      "cronbach_alpha": 0.87,
      "created_at": "2026-03-21T10:30:00",
      "completed_at": "2026-03-21T10:35:00"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses

**Example:**
```bash
curl "http://localhost:5000/api/rasch/analyses?course_id=1&status=completed"
```

---

### GET `/analyses/:id`

Get analysis detail.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Analysis ID |

**Response:**
```json
{
  "success": true,
  "analysis": {
    "id": 1,
    "name": "Mid Term Exam Analysis",
    "status": "completed",
    "progress_percentage": 100.0,
    "status_message": null,
    "started_at": "2026-03-21T10:30:00",
    "completed_at": "2026-03-21T10:35:00",
    "num_persons": 45,
    "num_items": 30,
    "cronbach_alpha": 0.87,
    "person_separation_index": 2.5,
    "item_separation_index": 3.2
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Analysis tidak ditemukan

**Example:**
```bash
curl http://localhost:5000/api/rasch/analyses/1
```

---

### GET `/analyses/:id/status`

Poll analysis status (untuk real-time updates).

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Analysis ID |

**Response:**
```json
{
  "success": true,
  "status": "processing",
  "progress_percentage": 45.5,
  "status_message": "Iteration 23/100",
  "is_complete": false,
  "is_failed": false,
  "started_at": "2026-03-21T10:30:00",
  "completed_at": null
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Analysis tidak ditemukan

**Example:**
```bash
curl http://localhost:5000/api/rasch/analyses/1/status
```

---

### DELETE `/analyses/:id`

Delete analysis.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Analysis ID |

**Response:**
```json
{
  "success": true,
  "message": "Analisis berhasil dihapus"
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Analysis tidak ditemukan

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/rasch/analyses/1
```

---

## Results Endpoints

### GET `/analyses/:id/persons`

Get person measures (ability θ) untuk semua siswa.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Analysis ID |
| student_id | integer | query | No | Filter by specific student |
| format | string | query | No | Response format (json/csv) |

**Response:**
```json
{
  "success": true,
  "analysis_id": 1,
  "count": 45,
  "persons": [
    {
      "student_id": 101,
      "student_name": "Ahmad",
      "raw_score": 85,
      "total_possible": 100,
      "percentage": 85.0,
      "theta": 1.23,
      "theta_se": 0.15,
      "theta_centered": 0.98,
      "ability_level": "high",
      "ability_percentile": 78.5,
      "fit_status": "well_fitted",
      "fit_category": "excellent",
      "outfit_mnsq": 0.95,
      "outfit_zstd": -0.5,
      "infit_mnsq": 1.02,
      "infit_zstd": 0.2
    }
  ]
}
```

**CSV Format:**
```
student_id,student_name,raw_score,percentage,theta,ability_level,ability_percentile,fit_status
101,Ahmad,85,85.0,1.23,high,78.5,well_fitted
102,Budi,70,70.0,0.15,average,52.3,well_fitted
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Analysis tidak ditemukan

**Example:**
```bash
# JSON
curl http://localhost:5000/api/rasch/analyses/1/persons

# CSV
curl "http://localhost:5000/api/rasch/analyses/1/persons?format=csv"
```

---

### GET `/analyses/:id/items`

Get item measures (difficulty δ) untuk semua soal.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Analysis ID |
| format | string | query | No | Response format (json/csv) |

**Response:**
```json
{
  "success": true,
  "analysis_id": 1,
  "count": 30,
  "items": [
    {
      "question_id": 1,
      "question_text": "Apa ibu kota Indonesia?",
      "delta": -1.5,
      "delta_se": 0.25,
      "difficulty_level": "easy",
      "p_value": 0.85,
      "point_biserial": 0.42,
      "bloom_level": "remember",
      "fit_status": "well_fitted",
      "fit_category": "excellent",
      "outfit_mnsq": 0.98,
      "infit_mnsq": 1.01
    }
  ]
}
```

**CSV Format:**
```
question_id,question_text,delta,difficulty_level,p_value,point_biserial,bloom_level,fit_status
1,Apa ibu kota Indonesia?,-1.5,easy,0.85,0.42,remember,well_fitted
2,Jelaskan penyebab...,0.5,moderate,0.65,0.38,analyze,well_fitted
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Analysis tidak ditemukan

**Example:**
```bash
# JSON
curl http://localhost:5000/api/rasch/analyses/1/items

# CSV
curl "http://localhost:5000/api/rasch/analyses/1/items?format=csv"
```

---

### GET `/analyses/:id/wright-map`

Get Wright Map visualization data.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Analysis ID |

**Response:**
```json
{
  "success": true,
  "analysis_id": 1,
  "map_data": {
    "person_distribution": [
      {"level": "very_high", "range": "> 2.0", "count": 5},
      {"level": "high", "range": "0.5 to 2.0", "count": 10},
      {"level": "average", "range": "-0.5 to 0.5", "count": 20},
      {"level": "low", "range": "-2.0 to -0.5", "count": 8},
      {"level": "very_low", "range": "< -2.0", "count": 2}
    ],
    "item_distribution": [
      {"level": "very_easy", "range": "< -2.0", "count": 3},
      {"level": "easy", "range": "-2.0 to -0.5", "count": 8},
      {"level": "moderate", "range": "-0.5 to 0.5", "count": 12},
      {"level": "difficult", "range": "0.5 to 2.0", "count": 5},
      {"level": "very_difficult", "range": "> 2.0", "count": 2}
    ],
    "mean_person_theta": 0.25,
    "mean_item_delta": 0.0,
    "sd_person": 1.2,
    "sd_item": 0.8
  },
  "num_persons": 45,
  "num_items": 30
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Analysis tidak ditemukan

**Example:**
```bash
curl http://localhost:5000/api/rasch/analyses/1/wright-map
```

---

## Bloom Taxonomy Endpoints

### GET `/quizzes/:id/bloom-summary`

Get Bloom taxonomy distribution untuk quiz.

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| id | integer | path | Yes | Quiz ID |

**Response:**
```json
{
  "success": true,
  "quiz_id": 123,
  "total_questions": 30,
  "distribution": {
    "remember": {"count": 5, "percentage": 16.7},
    "understand": {"count": 8, "percentage": 26.7},
    "apply": {"count": 10, "percentage": 33.3},
    "analyze": {"count": 5, "percentage": 16.7},
    "evaluate": {"count": 2, "percentage": 6.7},
    "create": {"count": 0, "percentage": 0.0}
  },
  "cognitive_depth": "moderate"
}
```

**Cognitive Depth Values:**
- `low`: Lebih banyak soal level rendah (remember, understand)
- `moderate`: Seimbang antara level rendah dan tinggi
- `high`: Lebih banyak soal level tinggi (analyze, evaluate, create)

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: User tidak memiliki akses
- `404 Not Found`: Quiz tidak ditemukan

**Example:**
```bash
curl http://localhost:5000/api/rasch/quizzes/123/bloom-summary
```

---

## Error Responses

### Standard Error Format

```json
{
  "success": false,
  "message": "Error description"
}
```

### Common Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid parameters |
| 403 | Forbidden | User tidak memiliki akses |
| 404 | Not Found | Resource tidak ditemukan |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Examples

**403 Forbidden:**
```json
{
  "success": false,
  "message": "Anda tidak memiliki akses ke analisis ini"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "Analisis tidak ditemukan"
}
```

---

## Rate Limiting

API endpoints menggunakan rate limiting:

- **Default:** 100 requests per minute per user
- **Heavy endpoints:** 10 requests per minute (export CSV)

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1679400000
```

**429 Response:**
```json
{
  "success": false,
  "message": "Terlalu banyak percobaan. Coba lagi nanti."
}
```

---

## Client Libraries

### Python Example

```python
import requests

BASE_URL = 'http://localhost:5000/api/rasch'

# Login
session = requests.Session()
session.post('http://localhost:5000/login', data={
    'email': 'teacher@example.com',
    'password': 'password'
})

# Check threshold
response = session.get(f'{BASE_URL}/quizzes/123/threshold-status')
data = response.json()
print(f"Progress: {data['percentage']}%")

# Get person measures
response = session.get(f'{BASE_URL}/analyses/1/persons')
persons = response.json()['persons']

for person in persons:
    print(f"{person['student_name']}: θ={person['theta']}")
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:5000/api/rasch';

// Check threshold
async function checkThreshold(quizId) {
  const response = await fetch(`${BASE_URL}/quizzes/${quizId}/threshold-status`);
  const data = await response.json();
  console.log(`Progress: ${data.percentage}%`);
  return data;
}

// Get person measures
async function getPersonMeasures(analysisId) {
  const response = await fetch(`${BASE_URL}/analyses/${analysisId}/persons`);
  const data = await response.json();
  return data.persons;
}

// Poll status
async function pollStatus(analysisId, callback) {
  const interval = setInterval(async () => {
    const response = await fetch(`${BASE_URL}/analyses/${analysisId}/status`);
    const data = await response.json();
    
    callback(data);
    
    if (data.is_complete || data.is_failed) {
      clearInterval(interval);
    }
  }, 5000); // Poll every 5 seconds
}
```

---

## Best Practices

### 1. Polling Strategy

Untuk monitoring analysis progress:

```python
import time

def wait_for_analysis(analysis_id, timeout=300):
    """Wait for analysis to complete"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f'{BASE_URL}/analyses/{analysis_id}/status')
        data = response.json()
        
        if data['is_complete']:
            print("Analysis completed!")
            return data
        elif data['is_failed']:
            print("Analysis failed!")
            return None
        
        print(f"Progress: {data['progress_percentage']}%")
        time.sleep(10)  # Poll every 10 seconds
    
    print("Timeout!")
    return None
```

### 2. Error Handling

```python
def safe_api_call(endpoint):
    """Safe API call with error handling"""
    try:
        response = requests.get(f'{BASE_URL}{endpoint}')
        response.raise_for_status()
        data = response.json()
        
        if not data['success']:
            print(f"API error: {data['message']}")
            return None
        
        return data
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
```

### 3. Batch Requests

Untuk multiple analyses:

```python
from concurrent.futures import ThreadPoolExecutor

def get_all_analyses(course_id):
    """Get all analyses for a course"""
    # First, get list
    response = requests.get(f'{BASE_URL}/analyses?course_id={course_id}')
    analyses = response.json()['analyses']
    
    # Then, get details in parallel
    def get_detail(analysis):
        resp = requests.get(f'{BASE_URL}/analyses/{analysis["id"]}')
        return resp.json()['analysis']
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        details = list(executor.map(get_detail, analyses))
    
    return details
```

---

**API Reference ini dibuat untuk Aldudu Academy**  
**Version:** 1.0  
**Last Updated:** 2026-03-21
