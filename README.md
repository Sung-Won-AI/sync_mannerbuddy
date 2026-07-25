# sync_mannerbuddy

AI 기반 글로벌 비즈니스 매너 케어 플랫폼. 자세한 기획/코딩 규칙은 [claude.md](./claude.md) 참고.

## 구조

```
sync_mannerbuddy/
├── extension/   # [기능 1] Gmail 실시간 메일 문장 수정 (Chrome 확장, Vite + CRXJS + TS)
├── dashboard/   # [기능 3, 4] 주간 대시보드 · 복습/퀴즈 (React + Vite + TS)
└── backend/     # [기능 1~4] API 서버 (FastAPI)
```

- `extension`, `dashboard`는 pnpm workspace로 관리됩니다.
- `backend`는 별도 Python(FastAPI) 프로젝트입니다.

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
