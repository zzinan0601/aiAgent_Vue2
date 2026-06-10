import os
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse

from config import settings
from database import engine, Base
from agent.nodes import load_tools_from_mcp

def setup_logging():
    root = logging.getLogger()
    if root.handlers:
        return
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir  = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.setLevel(logging.INFO)
    root.addHandler(fh)
    root.addHandler(ch)

setup_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS few_shots TEXT DEFAULT '[]';"))
            conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS use_knowledge BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS temperature DOUBLE PRECISION DEFAULT 0.7;"))
            conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS doc_metadata JSONB DEFAULT '{}'::jsonb;"))
            conn.execute(text("ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS chunk_metadata JSONB DEFAULT '{}'::jsonb;"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rag_settings (
                    id INTEGER PRIMARY KEY,
                    chunk_size INTEGER DEFAULT 500,
                    chunk_overlap INTEGER DEFAULT 50,
                    retrieve_top_k INTEGER DEFAULT 10,
                    rerank_top_n INTEGER DEFAULT 3,
                    dense_weight DOUBLE PRECISION DEFAULT 0.7,
                    sparse_weight DOUBLE PRECISION DEFAULT 0.3
                );
            """))
            conn.execute(text("""
                INSERT INTO rag_settings (id, chunk_size, chunk_overlap, retrieve_top_k, rerank_top_n, dense_weight, sparse_weight)
                VALUES (1, 500, 50, 10, 3, 0.7, 0.3)
                ON CONFLICT (id) DO NOTHING;
            """))
            # Sparse 역인덱스 테이블 (하이브리드 RAG)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sparse_index (
                    id SERIAL PRIMARY KEY,
                    embedding_id INTEGER REFERENCES embeddings(id) ON DELETE CASCADE,
                    token_id INTEGER NOT NULL,
                    weight DOUBLE PRECISION NOT NULL
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sparse_token_id ON sparse_index(token_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sparse_embedding_id ON sparse_index(embedding_id);"))
            # 기존 rag_settings에 가중치 컬럼 추가 (마이그레이션)
            conn.execute(text("ALTER TABLE rag_settings ADD COLUMN IF NOT EXISTS dense_weight DOUBLE PRECISION DEFAULT 0.7;"))
            conn.execute(text("ALTER TABLE rag_settings ADD COLUMN IF NOT EXISTS sparse_weight DOUBLE PRECISION DEFAULT 0.3;"))
            logger.info("sessions, rag_settings, sparse_index 테이블 마이그레이션 추가/확인 완료")
    except Exception as e:
        logger.warning("데이터베이스 마이그레이션 확인 실패: " + str(e))
        
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("MCP 툴 목록 로드 중...")
    try:
        await load_tools_from_mcp()
        logger.info("MCP 툴 로드 완료")
    except Exception as e:
        logger.exception("MCP 툴 로드 실패")
    yield

app = FastAPI(
    title    = "AI Agent API",
    version  = "1.0.0",
    docs_url = None,
    redoc_url= None,
    lifespan = lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 차트 이미지 서빙
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")

# 로컬 Swagger
@app.get("/docs", include_in_schema=False)
def custom_swagger() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url         = "/openapi.json",
        title               = "AI Agent API",
        swagger_js_url      = "/static/swagger/swagger-ui-bundle.js",
        swagger_css_url     = "/static/swagger/swagger-ui.css",
        swagger_favicon_url = "/static/swagger/favicon.png",
    )

@app.get("/redoc", include_in_schema=False)
def custom_redoc() -> HTMLResponse:
    return get_redoc_html(
        openapi_url       = "/openapi.json",
        title             = "AI Agent API",
        redoc_js_url      = "/static/swagger/redoc.standalone.js",
        redoc_favicon_url = "/static/swagger/favicon.png",
    )

# 라우터 등록
from api.session import router as session_router
from api.chat    import router as chat_router
from api.rag     import router as rag_router
from api.tools   import router as tools_router

app.include_router(session_router, prefix="/api/session", tags=["Session"])
app.include_router(chat_router,    prefix="/api/chat",    tags=["Chat"])
app.include_router(rag_router,     prefix="/api/rag",     tags=["RAG"])
app.include_router(tools_router,   prefix="/api/tools",   tags=["Tools"])

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    print(333)
    logger.info("서버 시작 포트=" + str(settings.backend_port))
    uvicorn.run(
        app,
        host            = "0.0.0.0",
        port            = settings.backend_port,
        reload          = False,
        reload_excludes = ["../logs/*", "../charts/*"]
    )
