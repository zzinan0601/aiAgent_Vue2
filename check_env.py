"""
실행: python check_env.py
설치 환경 전체 점검
"""
import sys
import os

def check(label, fn):
    try:
        fn()
        print("  OK  " + label)
        return True
    except Exception as e:
        print("  NG  " + label + " -> " + str(e))
        return False

print("\n==============================")
print("  환경 점검")
print("==============================\n")
print("  Python: " + sys.version.split()[0])

print("\n[패키지]")
check("fastapi",       lambda: __import__("fastapi"))
check("sqlalchemy",    lambda: __import__("sqlalchemy"))
check("psycopg2",      lambda: __import__("psycopg2"))
check("pgvector",      lambda: __import__("pgvector"))
check("langchain",     lambda: __import__("langchain"))
check("langgraph",     lambda: __import__("langgraph"))
check("fastmcp",       lambda: __import__("fastmcp"))
check("FlagEmbedding", lambda: __import__("FlagEmbedding"))
check("torch",         lambda: __import__("torch"))
check("pypdf",         lambda: __import__("pypdf"))
check("docx",          lambda: __import__("docx"))
check("matplotlib",    lambda: __import__("matplotlib"))

print("\n[PostgreSQL]")
def check_pg():
    import psycopg2
    conn = psycopg2.connect(host="localhost", port=5432, dbname="aiagent", user="postgres", password="1234")
    conn.close()
check("PostgreSQL 연결", check_pg)

def check_pgvector():
    import psycopg2
    conn = psycopg2.connect(host="localhost", port=5432, dbname="aiagent", user="postgres", password="1234")
    cur  = conn.cursor()
    cur.execute("SELECT extname FROM pg_extension WHERE extname='vector'")
    assert cur.fetchone(), "pgvector 확장 없음"
    conn.close()
check("pgvector 확장", check_pgvector)

print("\n[Ollama]")
def check_ollama():
    import requests
    res    = requests.get("http://localhost:11434/api/tags", timeout=3)
    models = [m["name"] for m in res.json().get("models", [])]
    print("        모델: " + str(models))
check("Ollama 연결", check_ollama)

print("\n[HuggingFace 모델]")
base = os.path.dirname(os.path.abspath(__file__))
check("bge-m3 폴더",
      lambda: open(os.path.join(base, "models", "bge-m3", "config.json")))
check("bge-reranker 폴더",
      lambda: open(os.path.join(base, "models", "bge-reranker-v2-m3", "config.json")))

print("\n==============================\n")
