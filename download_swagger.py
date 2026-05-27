"""
인터넷 PC에서 실행 -> backend/static/swagger/ 파일 생성
폐쇄망에서 Swagger UI 로컬 서빙용
"""
import httpx
import os

os.makedirs("backend/static/swagger", exist_ok=True)

files = {
    "swagger-ui-bundle.js": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    "swagger-ui.css"      : "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    "redoc.standalone.js" : "https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js",
    "favicon.png"         : "https://fastapi.tiangolo.com/img/favicon.png",
}

for name, url in files.items():
    print("다운로드: " + name + " ...", end=" ")
    r = httpx.get(url, follow_redirects=True, timeout=60)
    with open("backend/static/swagger/" + name, "wb") as f:
        f.write(r.content)
    print("완료 (" + str(len(r.content) // 1024) + "KB)")

print("\n완료! backend/static/swagger/ 폴더를 폐쇄망 서버로 복사하세요.")
