# Manner Buddy Backend

국가별 비즈니스 문화 차이로 발생하는 커뮤니케이션 문제를 분석하는 Chrome 확장 프로그램용 백엔드 서버입니다.

## 주요 기능

- 이메일 표현 분석 API
- 개인정보 및 민감정보 마스킹
- AI 분석 서비스 연동
- 분석 결과 저장 및 조회
- 추천 표현 채택 기록
- 사용자별 통계 제공

## 기술 스택

- Python
- FastAPI
- Supabase
- OpenAI API
- Pytest
- Docker

## 실행 방법

### 1. 저장소 복제

```bash
git clone <repository-url>
cd manner-buddy-backend
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

```bash
cp .env.example .env
```

`.env`에 필요한 값을 입력합니다.

```env
APP_ENV=development
FRONTEND_ORIGIN=chrome-extension://EXTENSION_ID

SUPABASE_URL=
SUPABASE_SECRET_KEY=

OPENAI_API_KEY=
OPENAI_MODEL=

USE_MOCK_AI=true
```

### 5. 서버 실행

```bash
fastapi dev app/main.py
```

서버 주소:

```text
http://localhost:8000
```

API 문서:

```text
http://localhost:8000/docs
```

## 주요 API

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/health` | 서버 상태 확인 |
| POST | `/api/v1/analyses/email` | 이메일 표현 분석 |
| GET | `/api/v1/analyses` | 분석 이력 조회 |
| GET | `/api/v1/analyses/{id}` | 분석 상세 조회 |
| POST | `/api/v1/analyses/{id}/actions` | 추천 표현 채택 기록 |
| GET | `/api/v1/dashboard/summary` | 사용자 통계 조회 |
| POST | `/api/v1/feedback` | 사용자 피드백 저장 |

## 테스트

```bash
pytest
```

## 프로젝트 구조

```text
app/
├── api/           # API 라우터
├── core/          # 설정, 인증, 오류 처리
├── schemas/       # 요청 및 응답 형식
├── services/      # 분석, AI, 마스킹 로직
├── repositories/  # 데이터베이스 접근
├── database/      # Supabase 연결
└── main.py        # 서버 시작점

tests/             # 테스트 코드
supabase/          # DB 마이그레이션
docs/              # API 및 연동 문서
extension-example/ # 확장 프로그램 연동 예제
```

## 주의사항

- `.env` 파일과 API 키는 GitHub에 업로드하지 않습니다.
- OpenAI API는 Chrome 확장 프로그램에서 직접 호출하지 않습니다.
- 실제 이메일 원문과 마스킹 전 개인정보는 로그에 저장하지 않습니다.
- 운영 환경에서는 등록된 확장 프로그램 ID만 허용합니다.
