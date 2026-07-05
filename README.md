# AI Agent 프로젝트

LangGraph 기반 AI 에이전트 + 하이브리드 RAG (Dense + Sparse) + AI 스킬 시스템 + FastMCP 툴 서버

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | Vue2, Vuex, Vue Router |
| Backend | FastAPI, LangChain, LangGraph |
| LLM 엔진 | Ollama (deepseek-r1:8b 등 동적 모델 선택 지원) |
| 임베딩 | BGE-M3 (Dense + Sparse, HuggingFace 로컬) |
| 리랭크 | BGE-Reranker-v2-m3 (HuggingFace 로컬) |
| 검색 융합 | RRF (Reciprocal Rank Fusion) |
| AI 스킬 | 동적 스킬 매뉴얼 탐색 및 주입 (`skills/` 디렉터리) |
| MCP | FastMCP 2.x / 3.x (SSE) |
| DB | PostgreSQL 16 + pgvector |

---

## 서비스 포트

| 서비스 | 포트 |
|--------|------|
| Vue2 Frontend | 3000 |
| FastAPI Backend | 8888 |
| FastMCP Server | 8889 |
| PostgreSQL | 5432 |
| Ollama | 11434 |

---

## 폴더 구조

```
project-root/
├── backend/                  FastAPI 백엔드 (8888)
│   ├── main.py               앱 진입점, 로컬 Swagger, 차트 서빙
│   ├── config.py             설정값 (.env 로드)
│   ├── database.py           PostgreSQL 연결
│   ├── .env                  환경변수
│   ├── api/
│   │   ├── chat.py           SSE 스트리밍 채팅 (astream_events)
│   │   ├── models.py         Ollama 모델 목록 조회 (/api/models/)
│   │   ├── rag.py            파일 업로드/임베딩/목록/삭제/청크조회
│   │   ├── session.py        세션 관리 및 AI 스킬 설정
│   │   └── tools.py          툴 목록 API (프론트 @ 자동완성용)
│   ├── agent/
│   │   ├── state.py          AgentState
│   │   ├── nodes.py          8개 노드 (분석/선택/실행/생성/평가/보완 + 스킬 매칭)
│   │   ├── graph.py          LangGraph 그래프
│   │   └── mcp_client.py     FastMCP 클라이언트
│   ├── models/models.py      ORM 모델
│   ├── rag/                  loader/chunker/embedder/retriever/model_loader
│   ├── schemas/              chat.py / rag.py
│   └── static/swagger/       Swagger UI 로컬 파일 (폐쇄망용)
│
├── mcp_server/               FastMCP SSE 서버 (8889)
│   ├── main.py               FastMCP 진입점
│   ├── config.py             MCP 전용 설정
│   ├── logger.py             로그 설정
│   ├── .env                  MCP 환경변수
│   ├── tools/                툴 (LLM 없음, 순수 데이터/액션)
│   │   ├── report_tool.py    DB조회 + 차트생성
│   │   ├── document_query_tool.py  벡터 문서 검색
│   │   └── db_query_tool.py  DB SQL 직접 조회
│   └── modules/              재사용 모듈
│       ├── db_query.py / vector_retrieve.py
│       ├── chart_generate.py / email_send.py
│       └── model_loader.py
│
├── frontend/                 Vue2 UI (3000)
│   └── src/
│       ├── views/            ChatView.vue / RagView.vue
│       ├── components/chat/  Sidebar/Window/Input/Dots/MessageItem/SessionContextModal/SessionSettingsModal
│       ├── components/rag/   FileUpload / DocList
│       └── store/ api/ router/
│
├── skills/                   AI 스킬 카탈로그 (동적 매뉴얼 주입)
│   └── standard_time_calculation_formula/  표준시간 산출공식 가이드 등
│
├── models/                   HuggingFace 로컬 모델
│   ├── bge-m3/
│   └── bge-reranker-v2-m3/
│
├── charts/                   생성된 차트 이미지 (백엔드 /charts 서빙)
├── logs/                     app.log / mcp.log
├── db/init.sql               DB 초기 스키마 (통합 명세 및 최신 기본값 적용)
├── requirements.txt          의존성 버전 고정 파일 (폐쇄망 호환)
├── download_models.py        HuggingFace 모델 다운로드
├── download_swagger.py       Swagger UI 파일 다운로드
├── check_env.py              환경 점검
├── start_all.bat             전체 서비스 실행
└── .gitignore
```

---

## 주요 핵심 기능

### 1. AI 스킬 시스템 (`skills/`)
- 사이드바의 **[스킬 사용]** 토글을 켜면, 사용자의 질문 의도에 맞춰 `skills/` 디렉터리에 정의된 전문 도메인 지식(SKILL.md)을 LLM이 동적으로 매칭하여 시스템 프롬프트에 주입합니다.
- 불필요한 전체 문서 주입 없이 필요한 텍스트만 낭비 없이 스마트하게 로드합니다.

### 2. 하이브리드 RAG 문서 관리 (`document_query_tool`)
- **지원 파일 형식**: **`PDF`, `DOCX`, `TXT`, `MD` (마크다운)**
- 문서 업로드 시 BGE-M3 모델을 통해 Dense(의미 검색) + Sparse(키워드 역인덱스) 임베딩을 동시 생성합니다.
- 검색 시 RRF(Reciprocal Rank Fusion) 알고리즘과 BGE Reranker를 통해 가장 관련도 높은 청크를 정확하게 추출합니다.

### 3. 실시간 컨텍스트 및 페르소나 제어
- **페르소나 & 퓨샷 설정**: 세션 설정 모달에서 맞춤형 시스템 프롬프트, Few-Shot 예시, 온도(Temperature, 기본값 `0.1`)를 동적으로 조율합니다.
- **컨텍스트 보기 모달**: AI 답변, 사용자 메시지, 툴 결합 프롬프트, 스킬 매뉴얼 주입 내역을 명확한 헤더와 함께 실시간으로 투명하게 확인할 수 있습니다.
- **Ollama 모델 선택**: 채팅 입력창에서 Ollama에 설치된 LLM 모델을 실시간으로 선택하여 대화할 수 있습니다.

---

## 에이전트 흐름

```
질문 입력
  → [analyze]       의도 분석 (일반대화 / 툴필요 / 툴목록) + 필요 시 스킬 매칭 주입
      → [llm_chat]  일반 LLM 응답 (토큰 스트리밍)
      → [tool_select] 툴 + 인자 결정
          → [tool_call] FastMCP Client -> MCP SSE 서버
              → [generate_answer] 툴별 전용 프롬프트로 LLM 답변 생성
                  → [evaluate] 품질 평가
                      → OK  -> 종료
                      → 부족 -> [refine] 답변 보완 후 재시도 (최대 2회)
```

---

## 실행 방법

### 사전 준비 (인터넷 PC)

```bash
# 모델 다운로드
python download_models.py

# Swagger UI 다운로드 (폐쇄망)
python download_swagger.py
```

### 폐쇄망 설치

```bash
# PostgreSQL + pgvector 설치 및 스키마 초기화
psql -U admin -d project_db -f db/init.sql

# Ollama 모델
ollama pull deepseek-r1:8b

# Python 패키지 (버전 충돌 방지 고정 완료)
pip install -r requirements.txt

# GPU torch (CUDA 버전 확인 후)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 환경 점검
python check_env.py
```

### 폐쇄망 오프라인 패키지 이동 및 설치 팁
```bash
# [인터넷 PC] 패키지 다운로드
pip download -r requirements.txt -d ./offline_wheels

# [폐쇄망 PC] 오프라인 설치
pip install --no-index --find-links=./offline_wheels -r requirements.txt
```

### 실행

```bash
start_all.bat
```

---

## 환경변수 (backend/.env)

```
DB_HOST=localhost / DB_PORT=5432 / DB_NAME=project_db
DB_USER=admin / DB_PASSWORD=admin1234
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=deepseek-r1:8b
EMBED_MODEL_PATH=models/bge-m3
RERANKER_MODEL_PATH=models/bge-reranker-v2-m3
USE_FP16=true
CHUNK_SIZE=500 / CHUNK_OVERLAP=50
RETRIEVE_TOP_K=10 / RERANK_TOP_N=3
BACKEND_PORT=8888 / MCP_PORT=8889
MCP_URL=http://localhost:8889/sse
UPLOAD_DIR=./uploads
```

*참고: `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVE_TOP_K`, `RERANK_TOP_N`은 서비스 초기 구동 시 데이터베이스(`rag_settings` 테이블)에 삽입되는 최초 설정값으로만 사용됩니다. 이후에는 **문서 관리 메뉴의 RAG 설정 화면에서 동적으로 조율하고 DB에서 로드**하여 적용하므로 실시간 변경이 가능합니다.*

---

## API 목록

| Method | URL | 설명 |
|--------|-----|------|
| POST | /api/chat/ | 채팅 SSE 스트리밍 |
| GET | /api/models/ | Ollama 사용 가능 모델 목록 조회 |
| GET | /api/session/ | 세션 목록 |
| POST | /api/session/ | 새 세션 (스킬 사용 옵션 지원) |
| PATCH | /api/session/{id} | 세션 설정 업데이트 (페르소나, 퓨샷, 스킬 토글, 온도) |
| GET | /api/session/{id}/messages | 대화 내용 |
| GET | /api/session/{id}/context | 실시간 대화 컨텍스트 전체 조회 |
| DELETE | /api/session/{id} | 세션 삭제 |
| POST | /api/rag/upload | 파일 업로드 (PDF, DOCX, TXT, MD) + 임베딩 |
| GET | /api/rag/list | 문서 목록 |
| GET | /api/rag/status/{id} | 임베딩 상태 |
| GET | /api/rag/{id}/chunks | 청크 내용 |
| DELETE | /api/rag/{id} | 문서 삭제 |
| GET | /api/rag/settings | 글로벌 RAG 설정 조회 |
| PUT | /api/rag/settings | 글로벌 RAG 설정 수정 |
| GET | /api/tools/ | 툴 목록 (@ 자동완성) |
| GET | /charts/{filename} | 차트 이미지 |

---

## 로그

```bash
# 실시간 확인
powershell Get-Content -Path logs\app.log -Wait
powershell Get-Content -Path logs\mcp.log -Wait
```
