"""
인터넷 PC에서 실행 -> models/ 폴더 생성 -> 폐쇄망 서버로 복사
"""
from huggingface_hub import snapshot_download
import os

SAVE_DIR = "./models"
os.makedirs(SAVE_DIR, exist_ok=True)

models = {
    "bge-m3"            : "BAAI/bge-m3",
    "bge-reranker-v2-m3": "BAAI/bge-reranker-v2-m3"
}

for folder, repo_id in models.items():
    save_path = os.path.join(SAVE_DIR, folder)
    print("다운로드 중: " + repo_id + " -> " + save_path)
    snapshot_download(
        repo_id=repo_id,
        local_dir=save_path,
        local_dir_use_symlinks=False
    )
    print("완료: " + save_path)

print("\n모든 모델 다운로드 완료!")
print("models/ 폴더를 폐쇄망 서버 프로젝트 루트에 복사하세요.")
