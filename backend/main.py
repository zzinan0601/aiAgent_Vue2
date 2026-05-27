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
   
    Base.metadata.create_all(bind=engine)
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
