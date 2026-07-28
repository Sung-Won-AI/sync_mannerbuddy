Manner Buddy MVP API

## 1. 이메일 분석

`POST /api/v1/analyses/email`

```json
{
  "text": "Please send the contract by Friday.",
  "target_country": "JP",
  "language": "en",
  "source": "gmail",
  "mode": "manual",
  "client_request_id": "unique-id"
}
```

## 2. 회의록 분석

`POST /api/v1/meetings/transcript`

```json
{
  "title": "Partner meeting",
  "transcript": "Alice: You are wrong. Bob: Let's review the schedule.",
  "target_country": "JP",
  "language": "en",
  "client_request_id": "unique-id"
}
```

음성 파일은 AI/STT 담당자가 텍스트로 변환한 뒤 이 API에 전달합니다.

## 3. 대시보드

`GET /api/v1/dashboard/summary?period_days=7`

## 4. 맞춤형 퀴즈

`GET /api/v1/quizzes?limit=5`

`POST /api/v1/quizzes/{question_id}/answer`

```json
{
  "option_id": "A"
}
```

## 부가 API

- `GET /api/v1/analyses`: 최근 분석 이력
- `POST /api/v1/analyses/{analysis_id}/actions`: 추천 표현 채택 기록
- `POST /api/v1/feedback`: CBT 만족도 저장

