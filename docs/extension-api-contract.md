# Extension API Contract

## 이메일 분석

```http
POST /api/v1/analyses/email
Content-Type: application/json
X-Extension-Version: 0.1.0
X-Request-ID: UUID
```

### 요청

```json
{
  "text": "Please send the contract by Friday.",
  "target_country": "JP",
  "language": "en",
  "source": "gmail",
  "mode": "manual",
  "client_request_id": "UUID"
}
```

지원 국가 코드는 `US`, `JP`, `CN`입니다.

### 성공 응답

```json
{
  "analysis_id": "UUID",
  "status": "completed",
  "request_id": "UUID",
  "overall_score": 72,
  "scores": {
    "vocabulary": 80,
    "tone": 55,
    "taboo": 90,
    "manners": 65
  },
  "issues": [
    {
      "issue_id": "UUID",
      "original": "Please send the contract by Friday.",
      "start_index": 0,
      "end_index": 39,
      "category": "tone",
      "severity": "medium",
      "reason": "다소 직접적인 요청으로 들릴 수 있습니다.",
      "suggestion": "Would it be possible to send the contract by Friday?"
    }
  ],
  "revised_text": "Would it be possible to send the contract by Friday?",
  "summary": "요청 표현을 조금 더 간접적으로 조정하는 것이 좋습니다.",
  "processing_time_ms": 5,
  "created_at": "2026-07-26T00:00:00Z"
}
```

### 오류 응답

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "요청값을 확인해주세요.",
    "details": {},
    "request_id": "UUID"
  }
}
```
