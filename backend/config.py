from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    db_host    : str = "localhost"
    db_port    : int = 5432
    db_name    : str = "aiagent"
    db_user    : str = "postgres"
    db_password: str = "1234"
    ollama_base_url    : str  = "http://localhost:11434"
    llm_model          : str  = "ministral-3:3b"
    embed_model_path   : str  = "models/bge-m3"
    reranker_model_path: str  = "models/bge-reranker-v2-m3"
    use_fp16           : bool = True
    chunk_size   : int = 500
    chunk_overlap: int = 50
    retrieve_top_k: int = 10
    rerank_top_n  : int = 3
    backend_port: int = 8888
    mcp_port    : int = 8889
    mcp_url     : str = "http://localhost:8889/sse"
    upload_dir  : str = "./uploads"

    class Config:
        env_file = ".env"

    @property
    def db_url(self) -> str:
        return (
            "postgresql://" + self.db_user + ":" + self.db_password +
            "@" + self.db_host + ":" + str(self.db_port) + "/" + self.db_name
        )

    @property
    def embed_model_abs_path(self) -> str:
        base = Path(__file__).resolve().parent.parent
        return (base / self.embed_model_path).as_posix()

    @property
    def reranker_model_abs_path(self) -> str:
        base = Path(__file__).resolve().parent.parent
        return (base / self.reranker_model_path).as_posix()

settings = Settings()
