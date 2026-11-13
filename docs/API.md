# API Documentation & Initial Contracts

**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Interactive Docs:** `http://127.0.0.1:8000/docs` (Swagger UI) / `http://127.0.0.1:8000/redoc` (ReDoc)  
**Version:** v1 (Phase 1 Foundation)  

---

## 1. System Health & Diagnostics

### `GET /api/v1/health`
Returns aggregate health status for the API service, database engine, and ML interfaces.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2026-11-13T10:35:00Z",
  "version": "0.1.0",
  "components": {
    "api_gateway": {
      "status": "healthy",
      "message": "FastAPI service is running and accepting requests.",
      "details": null
    },
    "database": {
      "status": "healthy",
      "message": "Database connection verified.",
      "details": {
        "dialect": "sqlite"
      }
    },
    "ml_engine": {
      "status": "healthy",
      "message": "ML subsystem interface initialized (Phase 1 foundation ready).",
      "details": null
    }
  }
}
```

---

### `GET /api/v1/health/database`
Executes an explicit database ping (`SELECT 1`) to verify engine connectivity.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "connected": true,
  "dialect": "sqlite",
  "url_type": "sqlite",
  "message": "Database ping successful",
  "timestamp": "2026-11-13T10:35:00Z"
}
```

---

## 2. Transactions

### `GET /api/v1/transactions`
Retrieves a paginated list of ingested transactions.

#### Query Parameters:
- `limit` (integer, default `50`, min `1`, max `500`)
- `offset` (integer, default `0`, min `0`)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Transactions endpoint ready. Ingestion pipeline will populate records in Phase 2.",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 50,
    "total_pages": 0
  }
}
```

### `POST /api/v1/transactions`
Validates and registers a transaction in the streaming ingestion pipeline.

#### Request Body
```json
{
  "transaction_id": "TXN_109283",
  "sender_account_id": "ACC_4892019283",
  "receiver_account_id": "ACC_1928301928",
  "amount": 49000.00,
  "currency": "INR",
  "transaction_type": "UPI",
  "timestamp": "2026-11-13T10:15:30Z",
  "channel": "mobile_app",
  "location": "Lucknow, Uttar Pradesh",
  "transaction_status": "COMPLETED"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "message": "Transaction validated successfully according to data contract.",
  "data": {
    "transaction_id": "TXN_109283",
    "sender_account_id": "ACC_4892019283",
    "receiver_account_id": "ACC_1928301928",
    "amount": 49000.0,
    "currency": "INR",
    "transaction_type": "UPI",
    "timestamp": "2026-11-13T10:15:30Z",
    "channel": "mobile_app",
    "location": "Lucknow, Uttar Pradesh",
    "transaction_status": "COMPLETED"
  }
}
```

---

## 3. Security Alerts

### `GET /api/v1/alerts`
Retrieves security alerts filtered by severity or status.

#### Query Parameters:
- `severity` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `status` (`OPEN`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`)
- `limit` (integer, default `50`)
- `offset` (integer, default `0`)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Alerts endpoint active. Alert triggers will be dispatched by scoring pipeline in Phase 2.",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 50,
    "total_pages": 0
  }
}
```

---

## 4. Detection Module Status Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/fraud/status` | `GET` | Supervised fraud model status and supported architectures |
| `/api/v1/anomaly/status` | `GET` | Behavioral anomaly detector and rolling window status |
| `/api/v1/aml/status` | `GET` | Supported AML graph typologies (structuring, cycles, fan-in/out) |
| `/api/v1/risk/status` | `GET` | Risk ensemble weights and score tier boundaries |
| `/api/v1/analytics/overview` | `GET` | System analytical performance KPIs |

