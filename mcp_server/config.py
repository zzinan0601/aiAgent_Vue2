from pydantic_settings import BaseSettings
from pathlib import Path

class MCPSettings(BaseSettings):
    db_host    : str = "localhost"
    db_port    : int = 5432
    db_name    : str = "project_db"
    db_user    : str = "admin"
    db_password: str = "admin1234"
    embed_model_path    : str  = "models/bge-m3"
    reranker_model_path : str  = "models/bge-reranker-v2-m3"
    use_fp16            : bool = True
    retrieve_top_k: int = 5
    mcp_port   : int = 8889
    chart_dir  : str = "../charts"
    backend_url: str = "http://localhost:8888"
    log_dir    : str = "../logs"

    class Config:
        env_file = ".env"

    @property
    def db_dsn(self) -> dict:
        return {
            "host": self.db_host, "port": self.db_port,
            "dbname": self.db_name, "user": self.db_user, "password": self.db_password
        }

    @property
    def embed_model_abs_path(self) -> str:
        base = Path(__file__).resolve().parent.parent
        return (base / self.embed_model_path).as_posix()

    @property
    def reranker_model_abs_path(self) -> str:
        base = Path(__file__).resolve().parent.parent
        return (base / self.reranker_model_path).as_posix()

    @property
    def chart_dir_abs(self) -> str:
        base = Path(__file__).resolve().parent
        return str((base / self.chart_dir).resolve())

    @property
    def chart_url_base(self) -> str:
        return self.backend_url + "/charts"

    @property
    def log_dir_abs(self) -> Path:
        base = Path(__file__).resolve().parent
        return (base / self.log_dir).resolve()

mcp_settings = MCPSettings()
