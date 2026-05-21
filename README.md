# 견적내드림

예산과 사용 목적에 맞춰 호환 가능한 조립 PC 견적을 추천하는 웹 애플리케이션입니다.

## 주요 기능

- 예산 / 목적 / 선호 브랜드 입력
- CPU, GPU, RAM, 저장장치, 메인보드, 쿨러, 파워, 케이스 조합 추천
- CSV 데이터셋 기반 가격 / 성능 / 호환성 반영
- `Compatibility_Pairs.csv` 기반 부품 호환성 검증
- 추천 견적 저장
- 대안 견적 비교
- 보관함 조회 / 삭제

## 기술 스택

- Frontend: Next.js, React, TypeScript
- Backend: FastAPI, Python
- Data: CSV 기반 PC 부품 / 가격 / 호환성 데이터셋

## 구조

- `frontend/`: Next.js App Router UI
- `backend/`: FastAPI API + 추천/검증 엔진

## 실행

백엔드 PowerShell:

```powershell
cd D:\BMVibe\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

가상환경을 활성화하지 않고 바로 실행하려면:

```powershell
cd D:\BMVibe\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

프론트엔드 PowerShell:

```powershell
cd D:\BMVibe\frontend
npm install
npm run dev
```

브라우저 접속:

- 프론트엔드: `http://127.0.0.1:3000`
- 백엔드 API 문서: `http://127.0.0.1:8000/docs`

프론트는 `NEXT_PUBLIC_API_BASE_URL`이 없으면 `http://localhost:8000/api/v1`을 사용합니다.

## 테스트

```bash
cd backend
python -m unittest discover -s tests
```

## 배포

- 서비스: https://quote-my-pc-llra.vercel.app
- 백엔드 API 문서: https://quote-my-pc-backend.onrender.com/docs

> Render 무료 플랜 특성상 백엔드가 잠들어 있으면 첫 요청이 느릴 수 있습니다.

## 데이터셋

현재 추천 엔진은 `backend/app/data/pc_dataset_augmented_price_compat_2026_05_csv/`의 CSV 파일을 사용합니다.
가격 정보는 추정값이므로 실제 구매 전 실시간 가격 확인이 필요합니다.

원본 벤치마크 CSV 데이터 출처:
https://www.userbenchmark.com/page/developer

선택적으로 다나와 스크래퍼가 생성한 가격 CSV를 `backend/data/danawa_prices/`에 둘 수 있습니다.
예: `cpu_prices.csv`, `gpu_prices.csv`, `ram_prices.csv`, `ssd_prices.csv`

이 디렉터리는 Git에 포함하지 않습니다. CSV가 없으면 기본 데이터셋의 추정 가격을 그대로 사용합니다.
