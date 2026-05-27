import os
import uuid
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import mcp_settings

logger = logging.getLogger(__name__)
plt.rcParams["font.family"]       = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

def _save(fig, title: str) -> dict:
    chart_dir = mcp_settings.chart_dir_abs
    os.makedirs(chart_dir, exist_ok=True)
    filename = uuid.uuid4().hex + ".png"
    path     = os.path.join(chart_dir, filename)
    url      = mcp_settings.chart_url_base + "/" + filename
    plt.title(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    logger.info("[chart] 저장: " + path)
    logger.info("[chart] URL: " + url)
    return {"path": path, "url": url}

def generate_bar_chart(labels: list, values: list, title: str = "차트") -> dict:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values, color="steelblue")
    ax.set_xlabel("항목")
    ax.set_ylabel("값")
    return _save(fig, title)

def generate_line_chart(labels: list, values: list, title: str = "추이") -> dict:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(labels, values, marker="o", color="steelblue", linewidth=2)
    ax.set_xlabel("기간")
    ax.set_ylabel("값")
    return _save(fig, title)
