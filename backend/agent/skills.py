"""
스킬(Skill) 로더 모듈
- skills/ 폴더 내 SKILL.md 파일을 스캔하여 YAML frontmatter(name, description)를 파싱
- 서버 기동 시 카탈로그(요약) 로드, 필요 시 본문 전체 로드
"""
import os
import logging

logger = logging.getLogger(__name__)

# 스킬 디렉토리 기본 경로 (backend/ 기준 상위의 skills/)
SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "skills")

_skill_catalog: list = []


def _parse_frontmatter(filepath: str) -> dict:
    """SKILL.md 파일에서 YAML frontmatter(--- 블록)를 파싱합니다."""
    meta = {"name": "", "description": "", "path": filepath}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.startswith("---"):
            return meta

        end_idx = content.index("---", 3)
        yaml_block = content[3:end_idx].strip()

        for line in yaml_block.splitlines():
            line = line.strip()
            if line.startswith("name:"):
                meta["name"] = line[5:].strip().strip('"').strip("'")
            elif line.startswith("description:"):
                meta["description"] = line[12:].strip().strip('"').strip("'")
    except Exception as e:
        logger.warning("[skills] frontmatter 파싱 실패: " + filepath + " " + str(e))

    return meta


def load_skill_catalog() -> list:
    """skills/ 하위 폴더를 스캔하여 모든 SKILL.md의 메타데이터를 로드합니다."""
    global _skill_catalog
    _skill_catalog = []

    if not os.path.isdir(SKILLS_DIR):
        logger.info("[skills] 스킬 디렉토리 없음: " + SKILLS_DIR + " (빈 카탈로그)")
        return _skill_catalog

    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, entry)
        skill_file = os.path.join(skill_dir, "SKILL.md")
        if os.path.isdir(skill_dir) and os.path.isfile(skill_file):
            meta = _parse_frontmatter(skill_file)
            if meta["name"]:
                _skill_catalog.append(meta)
                logger.info("[skills] 로드: " + meta["name"] + " ← " + skill_file)

    logger.info("[skills] 총 " + str(len(_skill_catalog)) + "개 스킬 로드 완료")
    return _skill_catalog


def get_skill_catalog() -> list:
    """현재 메모리에 캐시된 스킬 카탈로그(name, description만)를 반환합니다."""
    return _skill_catalog


def load_skill_content(skill_name: str) -> str:
    """지정된 스킬의 SKILL.md 본문(frontmatter 제외)을 반환합니다."""
    for skill in _skill_catalog:
        if skill["name"] == skill_name:
            try:
                with open(skill["path"], "r", encoding="utf-8") as f:
                    content = f.read()

                # frontmatter 제거 후 본문만 반환
                if content.startswith("---"):
                    try:
                        end_idx = content.index("---", 3)
                        return content[end_idx + 3:].strip()
                    except ValueError:
                        return content
                return content
            except Exception as e:
                logger.error("[skills] 본문 로드 실패: " + skill_name + " " + str(e))
                return ""

    logger.warning("[skills] 스킬을 찾을 수 없음: " + skill_name)
    return ""
