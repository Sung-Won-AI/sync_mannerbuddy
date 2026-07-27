# sync_mannerbuddy

AI 기반 글로벌 비즈니스 매너 케어 플랫폼. 자세한 기획/코딩 규칙은 [claude.md](./claude.md) 참고.

## 구조

```
sync_mannerbuddy/
├── extension/          # [기능 1] Gmail 실시간 메일 문장 수정 (Chrome 확장, Vite + CRXJS + TS)
├── dashboard/           # [기능 2,3,4] 화상회의 요약 · 대시보드 · 복습/퀴즈 (React + Vite + TS)
├── backend/              # [기능 1~4] API 서버 (FastAPI)
│   └── app/
│       ├── api/            # 라우터: analyses(이메일 분석), health, dashboard, meeting_summary, review_quiz
│       ├── core/             # 설정(config), 요청 컨텍스트 미들웨어, 예외 처리
│       ├── schemas/            # 요청·응답 스키마 (pydantic)
│       ├── services/             # 분석 파이프라인 · AI 클라이언트 · 개인정보 마스킹
│       └── main.py
├── docs/                 # 프론트-백엔드 API 계약 문서
├── .env.example
└── pnpm-workspace.yaml
```

- `extension`, `dashboard`는 pnpm workspace로 관리됩니다.
- `backend`는 별도 Python(FastAPI) 프로젝트입니다.

### 기능별 구현 상태

| 기능 | 엔드포인트 | 상태 |
|---|---|---|
| ① 메일 실시간 교정 | `POST /api/v1/analyses/email` | ✅ 구현 — 마스킹 → AI 분석(Mock/Remote) → 복원. 계약: [docs/extension-api-contract.md](./docs/extension-api-contract.md) |
| ② 화상회의 요약 | `POST /api/meeting-summary` | 🚧 스텁 (TODO) |
| ③ 대시보드 | `GET /api/dashboard/weekly-summary` | 🚧 스텁 (TODO) |
| ④ 복습 & 퀴즈 | `GET /api/review/*` | 🚧 스텁 (TODO) |

## 시작하기

### 사전 준비
- Node.js 18+, pnpm
- Python 3.11+

### 설치

```bash
pnpm install

cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[dev]"
```

### 환경 변수
API 키/설정은 프로젝트 루트의 `.env` 하나로 통합 관리합니다 (`backend`, `dashboard`, `extension`이 모두 이 파일을 공유). 루트의 `.env.example`을 복사해 `.env`를 만들고 값을 채워주세요. `.env`는 절대 git에 커밋하지 않습니다.

```bash
cp .env.example .env
```

`USE_MOCK_AI=true`(기본값)이면 실제 AI 호출 없이 Mock 분석 결과를 반환합니다. 실제 AI 연동은 `AI_SERVICE_URL`/`AI_SERVICE_API_KEY`를 채우고 `USE_MOCK_AI=false`로 바꾸면 됩니다.

### 실행

```bash
# 대시보드
pnpm dev:dashboard

# Chrome 확장 (개발 빌드 후 chrome://extensions 에서 dist 폴더 로드)
pnpm dev:extension

# 백엔드
cd backend
uvicorn app.main:app --reload
```

### 타입체크 / 테스트

```bash
pnpm typecheck            # extension, dashboard
cd backend && pytest      # backend
```

## 주의사항

- `.env` 파일과 API 키는 GitHub에 업로드하지 않습니다 (`.gitignore`에 등록됨).
- AI 서비스 키는 백엔드에서만 사용하고, Chrome 확장에서 직접 호출하지 않습니다.
- 실제 이메일 원문과 마스킹 전 개인정보(이메일 주소·전화번호·금액 등)는 로그에 저장하지 않습니다.
