# PostgreSQL + pgvector 설치 가이드 (폐쇄망 / Windows)

---

## 1. PostgreSQL 설치

**인터넷 PC에서 다운로드**
- https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- PostgreSQL 16 Windows x86-64 인스톨러 다운로드

**폐쇄망 서버에서 설치**
```
설치 경로 : C:\Program Files\PostgreSQL\16
포트      : 5432
superuser : postgres / admin1234 (원하는 값으로 설정)
```

**환경변수 PATH 추가**
```
C:\Program Files\PostgreSQL\16\bin
```

---

## 2. pgvector 설치 (Windows 빌드)

**방법 A: 미리 빌드된 바이너리 (권장)**

https://github.com/pgvector/pgvector/releases 에서
Windows용 zip 다운로드 예) `pgvector-v0.7.0-pg16-windows-x64.zip`

압축 해제 후 파일 복사:
```
vector.dll      → C:\Program Files\PostgreSQL\16\lib\
vector.control  → C:\Program Files\PostgreSQL\16\share\extension\
vector--*.sql   → C:\Program Files\PostgreSQL\16\share\extension\
```

**방법 B: 소스 빌드 (Visual Studio 필요)**
```cmd
git clone https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

---

## 3. DB 초기화

```cmd
# DB 생성
psql -U postgres -c "CREATE DATABASE project_db;"
psql -U postgres -c "CREATE USER admin WITH PASSWORD 'admin1234';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE project_db TO admin;"

# 스키마 초기화 (pgvector 확장 포함)
psql -U admin -d project_db -f db/init.sql
```

또는 psql 접속 후 직접 실행:
```sql
\c project_db
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 4. PostgreSQL 서비스 관리

```cmd
# 서비스 시작
pg_ctl start -D "C:\Program Files\PostgreSQL\16\data"

# 서비스 상태 확인
pg_ctl status -D "C:\Program Files\PostgreSQL\16\data"

# Windows 서비스로 등록 (자동 시작)
pg_ctl register -N "postgresql-16" -D "C:\Program Files\PostgreSQL\16\data"
```

---

## 5. 연결 확인

```cmd
psql -U admin -d project_db -c "SELECT version();"
psql -U admin -d project_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

---

## 6. HuggingFace 모델 준비 (폐쇄망)

**인터넷 PC에서 실행:**
```bash
pip install huggingface_hub
python download_models.py
```

생성된 `models/` 폴더를 폐쇄망 서버 프로젝트 루트에 복사:
```
project-root/
  models/
    bge-m3/               ← BGE-M3 임베딩 모델
    bge-reranker-v2-m3/   ← BGE Reranker 모델
```

---

## 7. Swagger UI 로컬 파일 준비 (폐쇄망)

**인터넷 PC에서 실행:**
```bash
pip install httpx
python download_swagger.py
```

생성된 `backend/static/swagger/` 폴더를 복사:
```
backend/static/swagger/
  swagger-ui-bundle.js
  swagger-ui.css
  redoc.standalone.js
  favicon.png
```

---

## 8. Python 패키지 오프라인 설치

**인터넷 PC에서 다운로드:**
```cmd
download_packages.bat
```

**폐쇄망 서버에서 설치:**
```cmd
pip install --no-index --find-links=pip_packages -r requirements.txt
```

---

## 9. GPU / CPU 확인

```cmd
nvidia-smi
```

**CUDA 버전별 PyTorch 설치:**
```cmd
# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CPU 전용 (GPU 없을 때)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**설치 확인:**
```cmd
python -c "import torch; print(torch.cuda.is_available()); print(torch.__version__)"
```

---

## 10. 전체 환경 점검

```cmd
python check_env.py
```

모든 항목이 OK 로 나오면 준비 완료입니다.
