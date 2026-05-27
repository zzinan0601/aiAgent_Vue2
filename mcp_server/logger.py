import logging
import os
from logging.handlers import RotatingFileHandler
from config import mcp_settings

def setup_logging():
    root = logging.getLogger()
    if root.handlers:
        return
    log_dir = mcp_settings.log_dir_abs
    os.makedirs(log_dir, exist_ok=True)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh = RotatingFileHandler(
        os.path.join(log_dir, "mcp.log"),
        maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.setLevel(logging.INFO)
    root.addHandler(fh)
    root.addHandler(ch)
