# AI Agent 프로젝트

LangGraph 기반 AI 에이전트 + RAG + FastMCP 툴 서버

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | Vue2, Vuex, Vue Router |
| Backend | FastAPI, LangChain, LangGraph |
| LLM 엔진 | Ollama (deepseek-r1:8b) |
| 임베딩 | BGE-M3 (HuggingFace 로컬) |
| 리랭크 | BGE-Reranker-v2-m3 (HuggingFace 로컬) |
| MCP | FastMCP 2.x (SSE) |
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
│   │   ├── rag.py            파일 업로드/임베딩/목록/삭제/청크조회
│   │   ├── session.py        세션 관리
│   │   └── tools.py          툴 목록 API (프론트 @ 자동완성용)
│   ├── agent/
│   │   ├── state.py          AgentState
│   │   ├── nodes.py          8개 노드 (분석/선택/실행/생성/평가/보완)
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
│       ├── views/  ChatView.vue / RagView.vue
│       ├── components/chat/  Sidebar/Window/Input/Dots/MessageItem
│       ├── components/rag/   FileUpload / DocList
│       ├── store/ api/ router/
│
├── models/                   HuggingFace 로컬 모델
│   ├── bge-m3/
│   └── bge-reranker-v2-m3/
│
├── charts/                   생성된 차트 이미지 (백엔드 /charts 서빙)
├── logs/                     app.log / mcp.log
├── db/init.sql               DB 초기 스키마
├── requirements.txt
├── download_models.py        HuggingFace 모델 다운로드
├── download_swagger.py       Swagger UI 파일 다운로드
├── check_env.py              환경 점검
├── start_all.bat             전체 서비스 실행
└── .gitignore
```

---

## 에이전트 흐름

```
질문 입력
  → [analyze]       일반대화 / 툴필요 / 툴목록 판단
      → [llm_chat]  일반 LLM 응답 (토큰 스트리밍)
      → [tool_select] 툴 + 인자 결정
          → [tool_call] FastMCP Client -> MCP SSE 서버
              → [generate_answer] 툴별 전용 프롬프트로 LLM 답변 생성
                  → [evaluate] 품질 평가
                      → OK  -> 종료
                      → 부족 -> [refine] 재시도 (최대 2회)
```

---

## MCP 아키텍처

```
MCP 서버 (LLM 없음)       백엔드 에이전트 (모든 LLM)
  report_tool           →  _build_report_prompt
  document_query_tool   →  _build_document_query_prompt
  db_query_tool         →  _build_db_query_prompt
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
# PostgreSQL + pgvector 설치 (INSTALL.md 참고)
psql -U admin -d project_db -f db/init.sql

# Ollama 모델
ollama pull deepseek-r1:8b

# Python 패키지
pip install -r requirements.txt

# GPU torch (CUDA 버전 확인 후)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 환경 점검
python check_env.py
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

---

## API 목록

| Method | URL | 설명 |
|--------|-----|------|
| POST | /api/chat/ | 채팅 SSE 스트리밍 |
| GET | /api/session/ | 세션 목록 |
| POST | /api/session/ | 새 세션 |
| GET | /api/session/{id}/messages | 대화 내용 |
| DELETE | /api/session/{id} | 세션 삭제 |
| POST | /api/rag/upload | 파일 업로드 + 임베딩 |
| GET | /api/rag/list | 문서 목록 |
| GET | /api/rag/status/{id} | 임베딩 상태 |
| GET | /api/rag/{id}/chunks | 청크 내용 |
| DELETE | /api/rag/{id} | 문서 삭제 |
| GET | /api/tools/ | 툴 목록 (@ 자동완성) |
| GET | /charts/{filename} | 차트 이미지 |

---

## 로그

```bash
# 실시간 확인
powershell Get-Content -Path logs\app.log -Wait
powershell Get-Content -Path logs\mcp.log -Wait
```
